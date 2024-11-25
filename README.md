Took locations.py file from D.Terrell and created another script to extract solar details for each entry and populate the csv with num of panels, yearly energy, and solar area (All max values).

Next step to verify entries for both the locations and the solar analysis.

for locations can use - google maps, put lat,long in maps and check if it pinpoints to correct buidling (i checked a few, seems to be correct). Create a verification flag column.
for solar analysis can use the endpoint: https://solar-potential-kypkjw5jmq-uc.a.run.app/ (Note: area provided is roof area and not solar area. Also num panels and yearly energy may not be the max showcased on the interface - need clarification with TA/Prof). you can check the solar_json files for respective entries to cross-check.

These above two will be the deliverables with their respective csv.
