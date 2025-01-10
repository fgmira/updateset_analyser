import json
import logging
from typing import Any

import httpx

from celery import Celery, chain, chord, group
from celery.signals import worker_process_init
from celery.utils.log import get_task_logger
from openai import OpenAI

from app_settings import app_settings

BROKER_URL = f"pyamqp://{app_settings.CELERY_BROKER_USER}:{app_settings.CELERY_BROKER_PASSWORD.get_secret_value()}@{app_settings.CELERY_BROKER_HOST}:{app_settings.CELERY_BROKER_PORT}/"
RESULT_BACKEND_URL = f"redis://{app_settings.REDIS_HOST}:{app_settings.REDIS_PORT}/0"

logging.basicConfig(
    format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
)


class InvalidOpenAIResponse(Exception):
    pass


app = Celery(
    "updateset_analyser",
    broker=BROKER_URL,
    backend=RESULT_BACKEND_URL,
)

logger = get_task_logger(__name__)


@app.task(bind=True, default_retry_delay=30, max_retries=3)
def analyse_update_record(self, update_record: dict) -> tuple[dict, dict]:
    PROMPT = """## PERSONA
You are an IT change analyst. Your goal is to evaluate what is being changed in a ServiceNow instance. To do this, you will perform an analysis of best practices on objects that are being changed.

## INSTRUCTIONS
1. Analyze the object:
   - Identify object type and purpose
   - List all business rules and their triggers
   - Assess potential performance impact
   - Evaluate security implications

2. Create technical summary (max 200 words):
   - Focus on core functionality
   - Include business rule interactions
   - Specify technical dependencies
   - Use standard ServiceNow terminology

3. Determine change characteristics:
   - Identify change type (INSERT_OR_UPDATE/DELETE)
   - Classify object type
   - Note any special handling requirements

## OBJECT TO BE ANALYZED
The object to be analyzed is in the form of an XML that represents it as a record in a ServiceNow table:
```XML
{object}
```

## RESPONSE FORMAT
For valid analysis, respond with:
```json
{response_format}
```

## EXAMPLE SUMMARY
Business rule 'UpdateIncident' on Incident table, triggered on before update. Implements automatic assignment routing based on assignment rules stored in assignment_rules table. Contains database queries to assignment_rules and group_members tables. Includes error handling for missing configuration data.
"""
    RESPONSE_FORMAT = {
        "summary": "string",
        "change_type": "INSERT_OR_UPDATE|DELETE",
        "type": "string",
        "performance_impact": "string",
        "validation_status": "valid",
    }
    logger.info(f"Starting analysis of update record: {update_record["sys_id"]}")

    prompt = PROMPT.format(
        object=update_record["payload"],
        response_format=json.dumps(RESPONSE_FORMAT, indent=4),
    )
    logger.debug(f"Analyzing update record usin prompt: {prompt}")

    try:
        openai_client = OpenAI(api_key=app_settings.OPENAI_API_KEY.get_secret_value())
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
            ],
            max_tokens=1000,
            temperature=0.5,
        )
        response_content = response.choices[0].message.content
        if response_content is None:
            logger.error("Empty response from OpenAI", exc_info=True)
            raise InvalidOpenAIResponse("Empty response from OpenAI")
    except Exception as e:
        logger.error(f"Error while calling OpenAI: {e}", exc_info=True)
        self.retry()

    logger.debug(f"OpenAI response content: {response_content}")

    try:
        response_json = json.loads(
            response_content.replace("```json\n", "").replace("\n```", "")  # type: ignore
        )
    except Exception as e:
        logger.error(
            f"Error in parsing OpenAI json response {response_content}: {e}",
            exc_info=True,
        )
        self.retry()

    logger.debug(f"OpenAI response JSON: {response_json}")
    return {
        "sys_id": update_record["sys_id"],
        "update_set": {"value": update_record["update_set"]["value"]},
    }, response_json


@app.task(bind=True, default_retry_delay=30, max_retries=3)
def insert_analysis(self, argument: tuple[dict, dict]) -> tuple[dict, dict]:
    logger.info(f"Inserting analysis into ServiceNow: {argument}")
    update_record, response_json = argument
    analisys = f"""
    SUMMARY: {response_json['summary']}
    CHANGE TYPE: {response_json['change_type']}
    TYPE: {response_json['type']}
    PERFORMANCE IMPACT: {response_json['performance_impact']}
    VALIDATION STATUS: {response_json['validation_status']}
    """
    data = {
        "comments": analisys,
    }
    logger.debug(f"data: {json.dumps(data)}")
    try:
        logger.debug(
            f"Inserting analysis into ServiceNow for update record: {update_record["sys_id"]}"
        )
        with httpx.Client() as client:
            response = client.patch(
                url=f"{app_settings.SERVICE_NOW_URL}api/now/table/sys_update_xml/{update_record["sys_id"]}",
                headers={"Content-Type": "application/json"},
                auth=(
                    app_settings.SERVICE_NOW_USER,
                    app_settings.SERVICE_NOW_PASSWORD.get_secret_value(),
                ),
                json={
                    "comments": analisys,
                },
            )
            response.raise_for_status()
    except Exception as e:
        logger.error(
            f"Error while calling ServiceNow: {e} - {response.headers} - {response.json}",
            exc_info=True,
        )
        self.retry()
    logger.info(
        f"Analysis inserted into ServiceNow for update record: {update_record["sys_id"]}"
    )
    return update_record, {"analisys": analisys}


@app.task(bind=True, default_retry_delay=30, max_retries=3)
def analyse_update_set(self, argument: list[tuple[dict, dict]]) -> tuple[dict, dict]:
    logger.info(f"Starting analysis of update set: {argument}")
    PROMPT = """## PERSONA
You are an IT change analyst. Your goal is to evaluate what is being changed in a ServiceNow instance. To do this, you will perform an analysis of best practices on objects that are being changed.

## INSTRUCTIONS
1. You are receiving a list of summaries of objects that are being changed, along with information on the type of change (INSERT_OR_UPDATE or DELETE) and the type of object.
2. Analyze the summaries to determine:
   a) The overall purpose of the changes
   b) Technical implications
   c) Dependencies between objects
3. Evaluate relationships between objects based on:
   - Direct dependencies
   - Shared functionality
   - Data flow connections
4. Write a technical report (max 200 words) addressing:
   - Change overview
   - Technical impact
   - Implementation requirements
   - Potential risks
5. Provide specific approval conditions considering:
   - Technical feasibility
   - Risk mitigation measures
   - Required testing
6. Evaluate risk level (LOW/MEDIUM/HIGH) based on:
   - Scope of impact
   - Number of affected users
   - System criticality

## INPUT FORMAT
Summaries should be provided in the following format:
```
{input_format}
```

## RESPONSE FORMAT
```json
{response_format}
```

## LIST OF SUMMARIES
```
{summaries}
```"""
    INPUT_FORMAT = {
        "summary": "string",
        "change_type": "INSERT_OR_UPDATE|DELETE",
        "type": "string",
        "performance_impact": "string",
        "validation_status": "valid",
    }
    RESPONSE_FORMAT = {
        "technical_analysis": {
            "overview": "string",
            "relationships": ["string"],
            "implementation_requirements": ["string"],
        },
        "approval_conditions": ["string"],
        "impact": "LOW|MEDIUM|HIGH",
        "risk_justification": "string",
    }
    summaries_list = []
    x = 1
    update_set_sys_id = argument[0][0]["update_set"]["value"]
    for update_record, analisys in argument:
        summaries_list.append(f"OBJECT {x:03}: {analisys["analisys"]}\n")
        x += 1
        if update_set_sys_id != update_record["update_set"]["value"]:
            raise ValueError("Update set sys_id mismatch")
    prompt = PROMPT.format(
        summaries="".join(summaries_list),
        response_format=json.dumps(RESPONSE_FORMAT, indent=4),
        input_format=json.dumps(INPUT_FORMAT, indent=4),
    )
    logger.debug(f"Analyzing update set using prompt: {prompt}")

    try:
        openai_client = OpenAI(api_key=app_settings.OPENAI_API_KEY.get_secret_value())
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
            ],
            max_tokens=1000,
            temperature=0.5,
        )
        response_content = response.choices[0].message.content
        if response_content is None:
            logger.error("Empty response from OpenAI", exc_info=True)
            raise InvalidOpenAIResponse("Empty response from OpenAI")
    except Exception as e:
        logger.error(f"Error while calling OpenAI: {e}", exc_info=True)
        self.retry()

    logger.debug(f"OpenAI response content: {response_content}")

    try:
        response_json = json.loads(
            response_content.replace("```json\n", "").replace("\n```", "")  # type: ignore
        )
    except Exception as e:
        logger.error(
            f"Error in parsing OpenAI json response {response_content}: {e}",
            exc_info=True,
        )
        self.retry()

    logger.debug(f"OpenAI response JSON: {response_json}")
    return {"sys_id": update_set_sys_id}, response_json


@app.task(bind=True, default_retry_delay=30, max_retries=3)
def insert_update_set_analysis(self, argument: tuple[dict, dict]) -> None:
    logger.info(f"Inserting analysis into ServiceNow: {argument}")
    update_set, response_json = argument

    realtionships = []
    for relationship in response_json["technical_analysis"]["relationships"]:
        realtionships.append(f"\n\t- {relationship}")

    implementation_requirements = []
    for implementation_requirement in response_json["technical_analysis"][
        "implementation_requirements"
    ]:
        implementation_requirements.append(f"\n\t- {implementation_requirement}")

    approval_conditions = []
    for approval_condition in response_json["approval_conditions"]:
        approval_conditions.append(f"\n\t- {approval_condition}")

    analisys = f"""
    TECHNICAL ANALYSIS:
        OVERVIEW: {response_json['technical_analysis']['overview']}
        RELATIONSHIPS: {"".join(realtionships)}
        IMPLEMENTATION REQUIREMENTS: {"".join(implementation_requirements)}
    APPROVAL CONDITIONS: {"".join(approval_conditions)}
    IMPACT: {response_json['impact']}
    RISK JUSTIFICATION: {response_json['risk_justification']}
    """
    try:
        logger.debug(
            f"Inserting analysis into ServiceNow for update set: {update_set["sys_id"]}"
        )
        with httpx.Client() as client:
            response = client.patch(
                url=f"{app_settings.SERVICE_NOW_URL}api/now/table/sys_update_set/{update_set["sys_id"]}",
                headers={"Content-Type": "application/json"},
                auth=(
                    app_settings.SERVICE_NOW_USER,
                    app_settings.SERVICE_NOW_PASSWORD.get_secret_value(),
                ),
                json={
                    "description": analisys,
                },
            )
            response.raise_for_status()
    except Exception as e:
        logger.error(f"Error while calling ServiceNow: {e}", exc_info=True)
        self.retry()
    logger.info(
        f"Analysis inserted into ServiceNow for update set: {update_set["sys_id"]}"
    )


@app.task(bind=True, default_retry_delay=30, max_retries=3)
def get_updateset(self, update_set_sys_id: str) -> list[dict[str, Any]] | None:
    logger.info(f"Starting analysis of update set: {update_set_sys_id}")
    try:
        logger.debug(f"Fetching update records for update set: {update_set_sys_id}")
        with httpx.Client() as client:
            response = client.get(
                url=f"{app_settings.SERVICE_NOW_URL}api/now/table/sys_update_xml",
                params={"sysparm_query": f"update_set={update_set_sys_id}"},
                headers={"Content-Type": "application/json"},
                auth=(
                    app_settings.SERVICE_NOW_USER,
                    app_settings.SERVICE_NOW_PASSWORD.get_secret_value(),
                ),
            )
            response.raise_for_status()
        response_json = response.json()
        logger.debug(f"Update records fetched: {response_json}")
        return response_json["result"]
    except Exception as e:
        logger.error(f"Error while calling ServiceNow: {e}", exc_info=True)
        self.retry()
    logger.info(f"Finished analysis of update set: {update_set_sys_id}")


@app.task
def analyse_updateset(update_set_sys_id: str):
    logger.info(f"Starting analysis of update set: {update_set_sys_id}")

    pipe = chord(
        (
            chain(analyse_update_record.s(update_record) | insert_analysis.s())
            for update_record in get_updateset(update_set_sys_id)  # type: ignore
        ),
        chain(analyse_update_set.s() | insert_update_set_analysis.s()),
    )
    logger.debug(f"Group of tasks created: {pipe}")
    pipe.apply_async()
    logger.info(f"Finished analysis of update set: {update_set_sys_id}")
