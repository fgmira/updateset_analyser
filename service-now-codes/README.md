# Service Now Codes

This path contains the codes used in the Service Now instance.


## Table of Contents
file | description
--- | ---
sn_clear_analysis.js | Script that cleans the data resulting from the analysis process, as a way to help in the application testing process, cleaning test masses
sys_rest_message_65ae7785c3fe9210907a9a2ed40131f8.xml | REST message that sends the data to the analysis process
sys_rest_message_fn_86debb45c3fe9210907a9a2ed4013153.xml | REST message method that sends the data to the analysis process
sys_ui_action_5e4c9ae5c3be1610907a9a2ed40131a3 | UI action that sends the data to the analysis process

## How to use

1. Import the REST message `sys_rest_message_65ae7785c3fe9210907a9a2ed40131f8.xml` and the REST message method `sys_rest_message_fn_86debb45c3fe9210907a9a2ed4013153.xml` to the Service Now instance.
2. Import the UI action `sys_ui_action_5e4c9ae5c3be1610907a9a2ed40131a3` to the Service Now instance.
3. If necessary, run the script `sn_clear_analysis.js` to clean the data resulting from the analysis process in the Service Now instance as a Backgrond Script.