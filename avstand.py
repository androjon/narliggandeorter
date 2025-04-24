import streamlit as st
import json
import requests
import re
import math
import operator
#from import_ads_platsbanken import import_ads

@st.cache_data
def import_data(filename):
    with open(filename) as file:
        content = file.read()
    output = json.loads(content)
    return output

# @st.cache_data
# def import_plastbanken():
#     st.session_state_ad_data_platsbanken = import_ads()

def split_town_municipality(town_municipality):
    town_municipality_split = town_municipality.split(";")
    municipality_id = town_municipality_split[1]
    municipality_name = st.session_state.municipality_id_namn.get(municipality_id)
    town_split = town_municipality_split[0]
    city_name = ' '.join(re.split("_", town_split))
    town_with_municipality = f"{city_name.capitalize()} ({municipality_name.capitalize()})"
    return municipality_id, town_with_municipality, f"{municipality_name} kommun"

def create_link_municipality(id_municipality):
    group_list = []
    for g in st.session_state.selected_groups:
        group_list.append(f"5:{g}")
    group_string = ";".join(group_list)
    link = f"https://arbetsformedlingen.se/platsbanken/annonser?p={group_string}&l=3:{id_municipality}"
    return link

def create_link_all_selected():
    group_list = []
    for g in st.session_state.selected_groups:
        group_list.append(f"5:{g}")
    group_string = ";".join(group_list)
    location_list = []
    for l in st.session_state.included_locations:
        location_list.append(f"3:{l['municipality_id']}")
    location_string = ";".join(location_list)
    link = f"https://arbetsformedlingen.se/platsbanken/annonser?p={group_string}&l={location_string}"
    return link

def get_addnumbers_location(municipality_id):
    all_ads_location = [0, 0]
    for g in st.session_state.selected_groups:
        ads_platsbanken_group = st.session_state.all_relevant_groups_with_platsbanken_ads.get(g)
        if ads_platsbanken_group:
            ads_location = ads_platsbanken_group.get(municipality_id)
            if ads_location:
                all_ads_location[0] += ads_location

        ads_historical_group = st.session_state.all_relevant_groups_with_historical_ads.get(g)
        if ads_historical_group:
            ads_location = ads_historical_group.get(municipality_id)
            if ads_location:
                all_ads_location[1] += ads_location
    return all_ads_location

def get_addnumbers_similar(g):
    all_ads_locations = [0, 0]
    ads_platsbanken_group = st.session_state.all_relevant_groups_with_platsbanken_ads.get(g)
    for l in st.session_state.included_locations:
        municipality_id = l["municipality_id"]
        if ads_platsbanken_group:       
            ads_location = ads_platsbanken_group.get(municipality_id)
            if ads_location:
                all_ads_locations[0] += ads_location

        ads_historical_group = st.session_state.all_relevant_groups_with_historical_ads.get(g)
        if ads_historical_group:
                ads_location = ads_historical_group.get(municipality_id)
                if ads_location:
                    all_ads_locations[1] += ads_location
    return all_ads_locations

@st.fragment
def extract_ads_relevant_occupation_groups(selected_group):
    if st.session_state.similar:
        relevant_occupation_groups = [selected_group]
        for key in st.session_state.similar.keys():
            info_similar = st.session_state.occupationdata.get(key)
            occupation_group_id_similar = info_similar["occupation_group_id"]
            relevant_occupation_groups.append(occupation_group_id_similar)
    else:
        relevant_occupation_groups = [selected_group]

    st.session_state.all_relevant_groups_with_platsbanken_ads = {}
    st.session_state.all_relevant_groups_with_historical_ads = {}
    for g in relevant_occupation_groups:
        ads_platsbanken = st.session_state.ad_data_platsbanken.get(g)
        st.session_state.all_relevant_groups_with_platsbanken_ads[g] = ads_platsbanken
        ads_historical = st.session_state.ad_data_historical.get(g)
        st.session_state.all_relevant_groups_with_historical_ads[g] = ads_historical

def create_locations_with_ads(id_location):
    all_locations_with_links_adds = []

    municipality_id, town_with_municipality, municipality_name = split_town_municipality(id_location)
    link_location = create_link_municipality(municipality_id)
    addnumbers = get_addnumbers_location(municipality_id)
    location_with_link_addnumbers = {
        "town_with_municipality": town_with_municipality,
        "municipality": municipality_name,
        "municipality_id": municipality_id,
        "distance": 0,
        "ads": addnumbers,
        "link": link_location}
    all_locations_with_links_adds.append(location_with_link_addnumbers)
    
    list_relevant_locations = st.session_state.geodata.get(id_location)

    for l in list_relevant_locations:
        municipality_id, town_with_municipality, municipality_name = split_town_municipality(l["ort2_id"])
        link_location = create_link_municipality(municipality_id)
        addnumbers = get_addnumbers_location(municipality_id)
        location_with_link_addnumbers = {
            "town_with_municipality": town_with_municipality,
            "municipality": municipality_name,
            "municipality_id": municipality_id,
            "distance": l["avstånd"],
            "ads": addnumbers,
            "link": link_location}
        all_locations_with_links_adds.append(location_with_link_addnumbers)
    
    all_locations_with_links_adds = sorted(all_locations_with_links_adds, key = operator.itemgetter("distance"), reverse = False)
    return all_locations_with_links_adds

def fetch_data():
    st.session_state.occupationdata = import_data("all_valid_occupations_with_info_v25.json")
    for key, value in st.session_state.occupationdata.items():
        st.session_state.valid_occupations[value["preferred_label"]] = key
    st.session_state.locations_id = import_data("ort_namn_id.json")
    st.session_state.valid_locations = list(st.session_state.locations_id.keys())
    st.session_state.geodata = import_data("ort_ort_relevans.json")
    st.session_state.municipality_id_namn = import_data("kommun_id_namn.json")
    st.session_state.ad_data_historical = import_data("ssyk_kommun_annonser_2024.json")
    st.session_state.ad_data_platsbanken= import_data("platsbanken.json")
    #import_plastbanken()

def show_initial_information():
    st.logo("af-logotyp-rgb-540px.jpg")
    st.title("Annonsplanerare")
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
    if data['ads'][0] == 1:
        annons_er_plats = "annons"
    else:
        annons_er_plats = "annonser"
    if data['ads'][1] == 1:
        annons_er_hist = "annons"
    else:
        annons_er_hist = "annonser"
    link = f"{data['ads'][0]} {annons_er_plats} <a href='{data['link']}'>Platsbanken</a>"
    location_string = f"<p style='font-size:16px;'><strong>{data['town_with_municipality']}</strong><br />&emsp;&emsp;&emsp;<small>{link}</small><br />&emsp;&emsp;&emsp;<small>{data['ads'][1]} {annons_er_hist} 2024</small></p>"
    return location_string

def create_string_location(data):
    if data['ads'][0] == 1:
        annons_er_plats = "annons"
    else:
        annons_er_plats = "annonser"
    if data['ads'][1] == 1:
        annons_er_hist = "annons"
    else:
        annons_er_hist = "annonser"
    link = f"{data['ads'][0]} {annons_er_plats} <a href='{data['link']}'>Platsbanken</a>"
    location_string = f"<p style='font-size:16px;'><strong>{data['town_with_municipality']}</strong> {data['distance']} km<br />&emsp;&emsp;&emsp;<small>{link}</small><br />&emsp;&emsp;&emsp;<small>{data['ads'][1]} {annons_er_hist} 2024</small></p>"
    return location_string

def count_total_ad_numbers(locations):
    total_ads_now = 0
    total_ads_historical = 0
    added_municipality = []
    for l in locations:
        if not l["municipality_id"] in added_municipality:
            addnumbers = get_addnumbers_location(l["municipality_id"])
            total_ads_now += addnumbers[0]
            total_ads_historical += addnumbers[1]
            added_municipality.append(l["municipality_id"])
    return total_ads_now, total_ads_historical

def show_selectable_similar(data):
    with st.sidebar:
        selection = {}
        for k, v in data.items():
            name = k
            addnumbers = get_addnumbers_similar(v)
            name_with_ads = f"{name} ({addnumbers[0]}/{addnumbers[1]})"
            selection[name_with_ads] = v
        selected = st.pills("Välj en eller flera närliggande yrken", list(selection.keys()), selection_mode = "multi")
        if selected:
            for s in selected:
                group_id = selection.get(s)
                st.session_state.selected_groups.append(group_id)

def post_selected_occupation(id_occupation):
    info = st.session_state.occupationdata.get(id_occupation)

    occupation_name = info["preferred_label"]
    occupation_group = info["occupation_group"]
    occupation_group_id = info["occupation_group_id"]
    occupation_field = info["occupation_field"]

    field_string = f"{occupation_field} (yrkesområde)"
    group_string = f"{occupation_group} (yrkesgrupp)"
    occupation_string = f"{occupation_name} (yrkesbenämning)"

    if info["yrkessamling"]:
        yrkessamling = info["yrkessamling"]
    else:
        yrkessamling = None

    ssyk_code = occupation_group[0:4]

    if info["barometer_id"]:
        barometer = [f"{info['barometer_name']} (yrkesbarometeryrke)", info["barometer_above_ssyk"], info["barometer_part_of_ssyk"]]
    else:
        barometer = None

    if info["similar_occupations"]:
        st.session_state.similar = info["similar_occupations"]
    else:
        st.session_state.similar = None

    if barometer:
        tree = create_tree(field_string, group_string, occupation_string, barometer, ["group"], yrkessamling, license)
    else:
        tree = create_tree(field_string, group_string, occupation_string, None, ["group"], yrkessamling, license)
    st.markdown(tree, unsafe_allow_html = True)

    #choose_related_locations(tab_names[4])
    #Allt nedan här under en @st.fragment

    valid_locations = sorted(st.session_state.valid_locations)
    selected_location = st.selectbox(
        "Välj en ort",
        (valid_locations), placeholder = "", index = None)

    if selected_location:
        id_selected_location = st.session_state.locations_id.get(selected_location)

        extract_ads_relevant_occupation_groups(occupation_group_id)

        col1, col2 = st.columns(2)
        with col2:
            a, b, c = st.columns(3)
        st.write("---")
        col3, col4 = st.columns(2)
        st.write("---")

        st.session_state.selected_groups = [occupation_group_id]

        locations_with_ads = create_locations_with_ads(id_selected_location)

        with col1:
            data_selected_location = locations_with_ads[0]
            string_selected_location = create_string_chosen_location(data_selected_location)
            st.markdown(string_selected_location, unsafe_allow_html = True)

        relevant_locations_with_ads = locations_with_ads[1:]

        antal_orter = len(relevant_locations_with_ads)
        n = math.ceil(antal_orter / 2)

        locations_1 = relevant_locations_with_ads[:n]
        locations_2 = relevant_locations_with_ads[n:]

        st.session_state.included_locations = [data_selected_location]

        with col3:
            for l in locations_1:
                c, d = st.columns([3, 1])
                string_location = create_string_location(l)
                c.markdown(string_location, unsafe_allow_html = True)
                include = d.checkbox(l['municipality'], key = l["town_with_municipality"], value = False, label_visibility = "collapsed")
                if include:
                    st.session_state.included_locations.append(l)

        with col4:
            for l in locations_2:
                c, d = st.columns([3, 1])
                string_location = create_string_location(l)
                c.markdown(string_location, unsafe_allow_html = True)
                include = d.checkbox(l['municipality'], key = l["town_with_municipality"], value = False, label_visibility = "collapsed")
                if include:
                    st.session_state.included_locations.append(l)

        #På något sätt uppdatera listan med olika orter efter att liknande har lagts till.

        e, f = st.columns(2)

        if st.session_state.similar:
            add_similar = e.checkbox("Inkludera närliggande yrken", key = "inkludera", value = False)

        if add_similar:
            similiar_name_group_id = {}
            for key in st.session_state.similar.keys():
                info_similar = st.session_state.occupationdata.get(key)
                name_similar = info_similar["preferred_label"]
                occupation_group_id_similar = info_similar["occupation_group_id"]
                similiar_name_group_id[name_similar] = occupation_group_id_similar
            show_selectable_similar(similiar_name_group_id)

        link_all = create_link_all_selected()
        f.link_button(f"Platsbanken ALLA", link_all, icon = ":material/link:")


        st.session_state.all_ads_now, st.session_state.all_ads_historical = count_total_ad_numbers(st.session_state.included_locations)

        skillnad_nu = st.session_state.all_ads_now - data_selected_location['ads'][0]
        skillnad_historiska = st.session_state.all_ads_historical - data_selected_location['ads'][1]

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