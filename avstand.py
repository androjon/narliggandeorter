import streamlit as st
import json
import requests
import re
import math

@st.cache_data
def import_data(filename):
    with open(filename) as file:
        content = file.read()
    output = json.loads(content)
    return output

@st.cache_data
def fetch_number_of_ads(url):
    response = requests.get(url)
    data = response.text
    json_data = json.loads(data)
    data_total = json_data["total"]
    number_of_ads = list(data_total.values())[0]
    return number_of_ads

def create_link_addnumbers_municipality(id_group, id_municipality):
    adlink = "https://jobsearch.api.jobtechdev.se/search?"
    end = "&limit=0"
    url = adlink + "occupation-group=" + id_group + "&municipality=" + id_municipality + end
    number_of_ads = fetch_number_of_ads(url)
    link = f"https://arbetsformedlingen.se/platsbanken/annonser?p=5:{id_group}&q=&l=3:{id_municipality}"
    return link, number_of_ads

def split_town_municipality(town_municipality):
    town_municipality_split = town_municipality.split(";")
    municipality_id = town_municipality_split[1]
    municipality_name = st.session_state.municipality_id_namn.get(municipality_id)
    town_split = town_municipality_split[0]
    city_name = ' '.join(re.split("_", town_split))
    town_with_municipality = f"{city_name.capitalize()} ({municipality_name.capitalize()})"
    return municipality_id, town_with_municipality, f"{municipality_name} kommun"

def add_ads_occupationgroup(id_group, id_location):
    list_relevant_locations = st.session_state.geodata.get(id_location)
    all_historical_ads_group = st.session_state_ad_data.get(id_group)
    selected_municipality_id, selected_town_with_municipality, municipality_name = split_town_municipality(id_location)

    ads_historical_selected_location = all_historical_ads_group.get(selected_municipality_id)
    link_selected_location, ads_now_selected_location = create_link_addnumbers_municipality(id_group, selected_municipality_id)

    if not ads_historical_selected_location:
        ads_historical_selected_location = 0

    all_locations_with_links_adds = [{
        "town_with_municipality": selected_town_with_municipality,
        "municipality": municipality_name,
        "distance": 0,
        "relevance": "hög",
        "ads_historical": ads_historical_selected_location,
        "ads_now": ads_now_selected_location,
        "link": link_selected_location}]

    list_relevant_locations = sorted(list_relevant_locations, key = lambda x: x["avstånd"])

    for l in list_relevant_locations:
        municipality_id, town_with_municipality, municipality_name = split_town_municipality(l["ort2_id"])

        ads_historical = all_historical_ads_group.get(municipality_id)
        if not ads_historical:
            ads_historical = 0
        link, ads_now = create_link_addnumbers_municipality(id_group, municipality_id)

        relevant_location_with_links_adds = {
        "town_with_municipality": town_with_municipality,
        "municipality": municipality_name,
        "distance": l["avstånd"],
        "relevance": l["relevans"],
        "ads_historical": ads_historical,
        "ads_now": ads_now,
        "link": link}
        all_locations_with_links_adds.append(relevant_location_with_links_adds)
    return all_locations_with_links_adds

def fetch_data():
    st.session_state.occupationdata = import_data("all_valid_occupations_with_info_v25.json")
    for key, value in st.session_state.occupationdata.items():
        st.session_state.valid_occupations[value["preferred_label"]] = key
    st.session_state.locations_id = import_data("ort_namn_id.json")
    st.session_state.valid_locations = list(st.session_state.locations_id.keys())
    st.session_state.geodata = import_data("ort_ort_relevans.json")
    st.session_state_ad_data = import_data("ssyk_kommun_annonser_2024.json")
    st.session_state.municipality_id_namn = import_data("kommun_id_namn.json")

def show_initial_information():
    st.logo("af-logotyp-rgb-540px.jpg")
    st.title("Relevanta pendlingsorter")
    initial_text = "Ett försöka att erbjuda information/stöd för arbetsförmedlare när det kommer till GYR-Y (Geografisk och yrkesmässig rörlighet - Yrke)."
    st.markdown(f"<p style='font-size:12px;'>{initial_text}</p>", unsafe_allow_html=True)

def initiate_session_state():
    if "valid_occupations" not in st.session_state:
        st.session_state.valid_occupations = {}
        st.session_state.adwords_occupation = {}

def create_tree(field, group, occupation, barometer, bold, yrkessamling = None, reglerad = None):
    SHORT_ELBOW = "└─"
    SPACE_PREFIX = "&nbsp;&nbsp;&nbsp;&nbsp;"
    LONG_PREFIX = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    strings = [f"{field}"]
    if barometer:
        barometer_name = barometer[0]
        if "barometer" in bold:
            barometer_name = f"<strong>{barometer_name}</strong>"
    if "occupation" in bold:
        occupation = f"<strong>{occupation}</strong>"
    if "group" in bold:
        group = f"<strong>{group}</strong>"

    if yrkessamling == "Kultur":
        occupation = f"{occupation} hanteras av AF Kultur"
    elif yrkessamling == "Sjöfart":
        occupation = f"{occupation} hanteras av AF Sjöfart"

    if reglerad:
        occupation = f"{occupation} Reglerat yrke"

    if barometer:
        if barometer[1] == True:
            strings.append(f"{SHORT_ELBOW}  {barometer_name}")
            strings.append(f"{SPACE_PREFIX}{SHORT_ELBOW}  {group}")
            strings.append(f"{SPACE_PREFIX}{SPACE_PREFIX}{SHORT_ELBOW}  {occupation}")
        elif barometer[2] == True:
            strings.append(f"{SHORT_ELBOW}  {group}")
            strings.append(f"{SPACE_PREFIX}{SHORT_ELBOW}  {barometer_name}")
            strings.append(f"{SPACE_PREFIX}{SPACE_PREFIX}{SHORT_ELBOW}  {occupation}")
        else:
            strings.append(f"{SHORT_ELBOW}  {group}")
            strings.append(f"{LONG_PREFIX} {barometer_name}")
            strings.append(f"{LONG_PREFIX}{SHORT_ELBOW}  {occupation}")
    else:
        strings.append(f"{SHORT_ELBOW}  {group}")
        strings.append(f"{SPACE_PREFIX}{SHORT_ELBOW}  {occupation}")
    string = "<br />".join(strings)
    tree = f"<p style='font-size:16px;'>{string}</p>"
    return tree

def create_string_chosen_location(data):
    location_string = f"<p style='font-size:16px;'><strong>{data['town_with_municipality']}</strong><br />&emsp;&emsp;&emsp;<small>Annonser 2024 - {data['ads_historical']}</small></p>"
    return location_string

def create_string_location(data):
    location_string = f"<p style='font-size:16px;'><strong>{data['town_with_municipality']}</strong><br />&emsp;&emsp;&emsp;<small>{data['distance']} kilometer - {data['relevance'].upper()} relevans</small><br />&emsp;&emsp;&emsp;<small>Annonser 2024 - {data['ads_historical']}</small></p>"
    if data["relevance"] == "hög":
        hover_string = "Hög relevans: Närhet till stor ort med många platsannonser förra året och stor arbetskraft/befolkning"
    elif data["relevance"] == "medel":
        hover_string = "Medel relevans: Mindre orter, eller större orter som ligger längre bort"
    else:
        hover_string = "Låg relevans: Små orter med svagare möjligheter till jobb"
    return location_string, hover_string

def count_total_ad_numbers(locations):
    total_ads_now = 0
    total_ads_historical = 0
    added_municipality = []
    for l in locations:
        if not l["municipality"] in added_municipality:
            total_ads_now += l["ads_now"]
            total_ads_historical += l["ads_historical"]
            added_municipality.append(l["municipality"])
    return total_ads_now, total_ads_historical

def post_selected_occupation(id_occupation):
    info = st.session_state.occupationdata.get(id_occupation)

    occupation_name = info["preferred_label"]
    occupation_group = info["occupation_group"]
    occupation_group_id = info["occupation_group_id"]
    occupation_field = info["occupation_field"]
    if info["yrkessamling"]:
        yrkessamling = info["yrkessamling"]
    else:
        yrkessamling = None

    ssyk_code = occupation_group[0:4]

    if info["barometer_id"]:
        barometer = [f"{info['barometer_name']} (yrkesbarometeryrke)", info["barometer_above_ssyk"], info["barometer_part_of_ssyk"]]
    else:
        barometer = None

    field_string = f"{occupation_field} (yrkesområde)"
    group_string = f"{occupation_group} (yrkesgrupp)"

    occupation_string = f"{occupation_name} (yrkesbenämning)"
    if barometer:
        tree = create_tree(field_string, group_string, occupation_string, barometer, ["group"], yrkessamling, license)
    else:
        tree = create_tree(field_string, group_string, occupation_string, None, ["group"], yrkessamling, license)
    st.markdown(tree, unsafe_allow_html = True)

    valid_locations = sorted(st.session_state.valid_locations)
    selected_location = st.selectbox(
        "Välj en ort",
        (valid_locations), placeholder = "", index = None)

    if selected_location:
        id_selected_location = st.session_state.locations_id.get(selected_location)
        locations_with_ads = add_ads_occupationgroup(occupation_group_id, id_selected_location)

        col1, col2 = st.columns(2)

        with col1:
            data_selected_location = locations_with_ads[0]
            string_selected_location = create_string_chosen_location(data_selected_location)
            st.markdown(string_selected_location, unsafe_allow_html = True)
            st.link_button(f"{data_selected_location['municipality']} ({data_selected_location['ads_now']})", data_selected_location["link"], icon = ":material/link:", help = "Antal annonser i Platsbanken inom parentes för aktuell yrkesgrupp och kommun")

        with col2:
            a, b, c = st.columns(3)

        st.write("---")

        col3, col4 = st.columns(2)

        relevant_locations_with_ads = locations_with_ads[1:]

        antal_orter = len(relevant_locations_with_ads)
        n = math.ceil(antal_orter / 2)

        locations_1 = relevant_locations_with_ads[:n]
        locations_2 = relevant_locations_with_ads[n:]

        included_locations = []     

        with col3:
            for l in locations_1:
                string_location, hover_info = create_string_location(l)
                st.markdown(string_location, unsafe_allow_html = True, help = hover_info)

                include = st.checkbox("Inkludera i sökområde", key = l["town_with_municipality"], value = False)
                if include:
                    included_locations.append(l)
                st.link_button(f"{l['municipality']} ({l['ads_now']})", l["link"], icon = ":material/link:", help = "Inom parentes antal annonser i Platsbanken för aktuell yrkesgrupp och kommun")

        with col4:
            for l in locations_2:
                string_location, hover_info = create_string_location(l)
                st.markdown(string_location, unsafe_allow_html = True, help = hover_info)

                include = st.checkbox("Inkludera i sökområde", key = l["town_with_municipality"], value = False)
                if include:
                    included_locations.append(l)
                st.link_button(f"{l['municipality']} ({l['ads_now']})", l["link"], icon = ":material/link:", help = "Inom parentes antal annonser i Platsbanken för aktuell yrkesgrupp och kommun")

        st.session_state.all_ads_now, st.session_state.all_ads_historical = count_total_ad_numbers([data_selected_location] + included_locations)

        skillnad_nu = st.session_state.all_ads_now - data_selected_location['ads_now']
        skillnad_historiska = st.session_state.all_ads_historical - data_selected_location['ads_historical']

        a.metric(label = "Platsbanken", value = st.session_state.all_ads_now, delta = skillnad_nu, help = "Antal annonser i Platsbanken för aktuell yrkesgrupp och inkluderade kommuner. Siffran nedanför är antalet annonser i inkluderade närliggande kommuner.")
        b.metric(label = "2024", value = st.session_state.all_ads_historical, delta = skillnad_historiska, help = "Antal annonser 2024 för aktuell yrkesgrupp och inkluderade kommuner. Siffran nedanför är antalet annonser i inkluderade närliggande kommuner.")

        text_dataunderlag_närliggande_orter = "<strong>Dataunderlag</strong><br />Närliggande orter baseras på avstånd mellan orter från öppen geodata, annonser i Platsbanken och Historiska berikade annonser knutna till aktuell yrkesgrupp och kommun."
        
        st.write("---")
        st.markdown(f"<p style='font-size:12px;'>{text_dataunderlag_närliggande_orter}</p>", unsafe_allow_html=True)

def choose_occupation_name():
    show_initial_information()
    valid_occupations = list(st.session_state.valid_occupations.keys())
    valid_occupations = sorted(valid_occupations)
    selected_occupation_name = st.selectbox(
        "Välj en yrkesbenämning",
        (valid_occupations), placeholder = "", index = None)
    if selected_occupation_name:
        id_selected_occupation = st.session_state.valid_occupations.get(selected_occupation_name)
        post_selected_occupation(id_selected_occupation)

def main ():
    initiate_session_state()
    fetch_data()
    choose_occupation_name()

if __name__ == '__main__':
    main ()