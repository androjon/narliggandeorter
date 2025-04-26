import json
import requests

def get_api(query):
    response = requests.get(url = query)
    data = response.text
    json_data = json.loads(data)
    return json_data

def import_ads():
    jobstream = "https://jobstream.api.jobtechdev.se/snapshot"
    data = get_api(jobstream)

    output_ssyk_regions_municipalities = {}

    for ad in data:
        municipality_id = ad["workplace_address"]["municipality_concept_id"]
        region_id = ad["workplace_address"]["region_concept_id"]
        ssyk_id = ad["occupation_group"]["concept_id"]

        if municipality_id:
            if not ssyk_id in output_ssyk_regions_municipalities:
                output_ssyk_regions_municipalities[ssyk_id] = {}
            if not municipality_id in output_ssyk_regions_municipalities[ssyk_id]:
                output_ssyk_regions_municipalities[ssyk_id][municipality_id] = 0
            output_ssyk_regions_municipalities[ssyk_id][municipality_id] += 1

        if region_id:
            if not ssyk_id in output_ssyk_regions_municipalities:
                output_ssyk_regions_municipalities[ssyk_id] = {}
            if not region_id in output_ssyk_regions_municipalities[ssyk_id]:
                output_ssyk_regions_municipalities[ssyk_id][region_id] = 0
            output_ssyk_regions_municipalities[ssyk_id][region_id] += 1

    return output_ssyk_regions_municipalities