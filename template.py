"""
Script to provision a user template without using network profiles
"""

from __future__ import print_function
import dna
import logging
import json
import time
import base64

raw_input = vars(__builtins__).get('raw_input', input)  # Py2/3 compatibility

HOST = ""
USERNAME = ""
PASSWORD = ""
LOGGING = False

def main():
    if LOGGING:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')
    with dna.Dnac(HOST) as dnac:
        dnac.login(USERNAME, PASSWORD)
        # Get available templates
        templates = dnac.get("template-programmer/template")
        print("Templates:")
        for i, template in enumerate(templates):
            print(i, template.projectName, template.name)
        print('-'*80)
        idx = int(raw_input("Select template: "))
        # Find latest version of selected template
        latest = max(templates[idx].versionsInfo, key=lambda vi:vi.version)
        # Get template
        template = dnac.get("/template-programmer/template/" + latest.id)
        logging.debug("content=" + template.templateContent)
        params = {}
        if template.templateParams:
            print("Input template parameters:")
            for tp in template.templateParams:
                dtype = tp.dataType if tp.dataType else "STRING"
                dname = tp.displayName if tp.displayName else tp.parameterName
                # Make list of selection values, if any
                v = ""
                if tp.selection:
                    v = ", ".join(iter(tp.selection.selectionValues.values()))
                if not v:
                    # Make list of value ranges, if any
                    v = (", ".join("%d-%d" % (r.minValue, r.maxValue)
                                   for r in tp.range))
                # Compose user prompt for parameter value input
                prompt = ("%s %s [%s]" % (dtype, dname, v) if v else
                          "%s %s" % (dtype, dname))
                params[tp.parameterName] = raw_input("%s: " % prompt)
        else:
            print("Template takes no parameters")
        # Get network-devices
        devices = dnac.get("network-device").response
        print("Devices:")
        for i, device in enumerate(devices):
            print(i, device.hostname)
        print('-'*80)
        idx = int(raw_input("Select device: "))
        # Verify matching template device type
        if not dna.find(template.deviceTypes, devices[idx].family,
                        "productFamily"):
            print("Device type mismatch")
            return
        # Body
        data = {"targetInfo": [{"id": devices[idx].managementIpAddress,
                                "type": "MANAGED_DEVICE_IP",
                                "params": params}],
                "templateId": latest.id}
        logging.debug("data=" + json.dumps(data))
        response = dnac.post("template-programmer/template/deploy",
                             data=data).response
        print("Waiting for Task")
        task_result = dnac.wait_on_task(response.taskId).response
        print(task_result.progress)
        print("Completed in %s seconds" % (float(task_result.endTime
                                           - task_result.startTime) / 1000))
        
if __name__ == "__main__":
    main()
