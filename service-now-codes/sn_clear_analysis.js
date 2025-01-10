var gr_us = new GlideRecord("sys_update_set");
gr_us.query();
while (gr_us.next()) {
    gr_us.description = "";
    gr_us.update();
}

var gr_us_xml = new GlideRecord("sys_update_xml");
gr_us_xml.query();
while (gr_us_xml.next()) {
    gr_us_xml.comments = "";
    gr_us_xml.update();
}