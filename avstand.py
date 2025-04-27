import streamlit as st
import json
import requests
import itertools
import re
import operator
from import_ads_platsbanken import import_ads

@st.cache_data
def import_plastbanken():
    data = import_ads()
    return data

@st.cache_data
def import_data(filename):
    with open(filename) as file:
        content = file.read()
    output = json.loads(content)
    return output

def fetch_data():
    st.session_state.occupationdata = import_data("all_valid_occupations_with_info_v25.json")
    for key, value in st.session_state.occupationdata.items():
        st.session_state.valid_occupations[value["preferred_label"]] = key
    st.session_state.locations_id = import_data("ort_namn_id.json")
    st.session_state.valid_locations = list(st.session_state.locations_id.keys())
    st.session_state.geodata = import_data("ort_ort_relevans.json")
    st.session_state.municipality_id_namn = import_data("kommun_id_namn.json")
    st.session_state.ad_data_historical = import_data("ssyk_region_kommun_annonser_2024.json")
    st.session_state.ad_data_platsbanken = import_plastbanken()
    #st.session_state.ad_data_platsbanken = import_data("platsbanken.json")
    st.session_state.occupation_group_id_name = import_data("occupation_group_id_name.json")

def show_initial_information():
    st.logo("af-logotyp-rgb-540px.jpg")
    st.title("Annonsplanerare")
    initial_text = "Ett försöka att erbjuda information/stöd för arbetsförmedlare när det kommer till GYR-Y (Geografisk och yrkesmässig rörlighet - Yrke)."
    st.markdown(f"<p style='font-size:12px;'>{initial_text}</p>", unsafe_allow_html=True)

def initiate_session_state():
    if "valid_occupations" not in st.session_state:
        st.session_state.valid_occupations = {}
        st.session_state.adwords_occupation = {}

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
    for g in st.session_state.included_groups:
        group_list.append(f"5:{g}")
    group_string = ";".join(group_list)
    link = f"https://arbetsformedlingen.se/platsbanken/annonser?p={group_string}&l=3:{id_municipality}"
    return link

def create_link_group(group_id):
    location_list = []
    for municipality_id in st.session_state.included_municipalities:
        location_list.append(f"3:{municipality_id}")
    location_string = ";".join(location_list)
    link = f"https://arbetsformedlingen.se/platsbanken/annonser?p=5:{group_id}&l={location_string}"
    return link

def create_link_all_selected():
    group_list = []
    for g in st.session_state.included_groups:
        group_list.append(f"5:{g}")
    group_string = ";".join(group_list)
    location_list = []
    for municipality_id in st.session_state.included_municipalities:
        location_list.append(f"3:{municipality_id}")
    location_string = ";".join(location_list)
    link = f"https://arbetsformedlingen.se/platsbanken/annonser?p={group_string}&l={location_string}"
    return link

def get_addnumbers_location(municipality_id):
    all_ads_location = [0, 0]
    for g in st.session_state.included_groups:
        ads_platsbanken_group = st.session_state.ad_data_platsbanken.get(g)
        if ads_platsbanken_group:
            ads_location = ads_platsbanken_group.get(municipality_id)
            if ads_location:
                all_ads_location[0] += ads_location

        ads_historical_group = st.session_state.ad_data_historical.get(g)
        if ads_historical_group:
            ads_location = ads_historical_group.get(municipality_id)
            if ads_location:
                all_ads_location[1] += ads_location
    return all_ads_location

def get_addnumbers_similar(g):
    all_ads_locations = [0, 0]
    ads_platsbanken_group = st.session_state.ad_data_platsbanken.get(g)
    for municipality_id in st.session_state.included_municipalities:
        if ads_platsbanken_group:
            ads_location = ads_platsbanken_group.get(municipality_id)
            if ads_location:
                all_ads_locations[0] += ads_location

        ads_historical_group = st.session_state.ad_data_historical.get(g)
        if ads_historical_group:
            ads_location = ads_historical_group.get(municipality_id)
            if ads_location:
                all_ads_locations[1] += ads_location
    return all_ads_locations

def get_addnumbers_similar_relevant_locations(g, id_location):
    all_ads_similar = [0, 0]
    list_relevant_locations = st.session_state.geodata.get(id_location)
    ads_platsbanken_group = st.session_state.ad_data_platsbanken.get(g)
    ads_historical_group = st.session_state.ad_data_historical.get(g)
    if ads_platsbanken_group:
        for l in list_relevant_locations:
            municipality_id, town_with_municipality, municipality_name = split_town_municipality(l["ort2_id"])
            ads_location = ads_platsbanken_group.get(municipality_id)
            if ads_location:
                all_ads_similar[0] += ads_location
            ads_location = ads_historical_group.get(municipality_id)
            if ads_location:
                all_ads_similar[1] += ads_location
    return all_ads_similar

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

def create_string_location(data):
    annons_er_plats = "annons" if data['ads'][0] == 1 else "annonser"
    distance = "" if data['distance'] == 0 else f" {data['distance']} km"
    link = f"{data['ads'][0]} {annons_er_plats} <a href='{data['link']}'>Platsbanken</a> (2024: {data['ads'][1]})"
    return f"<p style='font-size:16px;'><strong>{data['town_with_municipality']}</strong>{distance}<br />&emsp;&emsp;&emsp;<small>{link}</small></p>"

def create_string_similar(data):
    name, occupation_group_id = list(data.items())[0]
    addnumbers = get_addnumbers_similar(occupation_group_id)
    annons_er_plats = "annons" if addnumbers[0] == 1 else "annonser"
    link = f"{addnumbers[0]} {annons_er_plats} <a href='{create_link_group(occupation_group_id)}'>Platsbanken</a> (2024: {addnumbers[1]})"
    return f"<p style='font-size:16px;'><strong>{name}</strong><br />&emsp;&emsp;&emsp;<small>{link}</small></p>", occupation_group_id

def create_string_all_selected():
    if st.session_state.all_ads_now == 1:
        annons_er_plats = "annons"
    else:
        annons_er_plats = "annonser"
    link = f"{st.session_state.all_ads_now} {annons_er_plats} <a href='{create_link_all_selected()}'>Platsbanken</a> (2024: {st.session_state.all_ads_historical})"
    string_all_selected = f"<p style='font-size:16px;'><strong>Alla inkluderade</strong><br />&emsp;&emsp;&emsp;<small>{link}</small></p>"
    return string_all_selected

def count_total_ad_numbers():
    total_ads_now = 0
    total_ads_historical = 0
    for m in st.session_state.included_municipalities:
            addnumbers = get_addnumbers_location(m)
            total_ads_now += addnumbers[0]
            total_ads_historical += addnumbers[1]
    return total_ads_now, total_ads_historical

def create_selectable_similar(id_location):
    similar_with_add_relevance = {}
    for key, value in st.session_state.similar.items():
        info_similar = st.session_state.occupationdata.get(key)
        name_similar = info_similar["preferred_label"]
        occupation_group_id_similar = info_similar["occupation_group_id"]
        addnumbers = get_addnumbers_similar_relevant_locations(occupation_group_id_similar, id_location)
        add_relevance = addnumbers[0] * 20 +  addnumbers[1]
        similar_with_add_relevance[add_relevance] = {name_similar: occupation_group_id_similar}
    sorted_similar_with_add_relevance = dict(sorted(similar_with_add_relevance.items(), reverse = True))
    top_ten_similar_with_add_relevance = dict(itertools.islice(sorted_similar_with_add_relevance.items(), 10))
    top_ten_similar = []
    for v in top_ten_similar_with_add_relevance.values():
        top_ten_similar.append(v)
    sorted_top_ten = sorted(top_ten_similar, key = lambda x: list(x.keys())[0])
    return sorted_top_ten

def update_location_ads_based_on_selection():
    for loc in st.session_state.relevant_locations_with_ads:
        municipality_id = loc['municipality_id']
        ads_total = [0, 0]

        for group_id in st.session_state.included_groups:
            platsbanken_data = st.session_state.ad_data_platsbanken.get(group_id, {})
            historical_data = st.session_state.ad_data_historical.get(group_id, {})

            if platsbanken_data:
                ads_total[0] += platsbanken_data.get(municipality_id, 0)
            if historical_data:
                ads_total[1] += historical_data.get(municipality_id, 0)

        loc['ads'] = ads_total  # 🔄 skriv över annonsvärden

def show_options():
    col3, col4 = st.columns(2)

    with col3:
        st.markdown(
            "<p style='font-size:16px;'><strong>Utöka sökområde geografiskt</strong></p>",
            unsafe_allow_html=True,
            help="Utöka sökområde geografiskt genom att välja orter i listan ned. Sökområdet uttökas med kommunen som orten ligger i."
        )

        for l in st.session_state.relevant_locations_with_ads:
            c, d = st.columns([3, 1])
            c.markdown(create_string_location(l), unsafe_allow_html=True)
            include = d.checkbox(
                l['municipality'],
                key=l["town_with_municipality"],
                value=l['municipality_id'] in st.session_state.included_municipalities,
                label_visibility="collapsed"
            )

            if include and l['municipality_id'] not in st.session_state.included_municipalities:
                st.session_state.included_municipalities.append(l['municipality_id'])
                st.rerun()
            elif not include and l['municipality_id'] in st.session_state.included_municipalities:
                st.session_state.included_municipalities.remove(l['municipality_id'])
                st.rerun()

    with col4:
        if st.session_state.selectable_similar:
            st.markdown(
                "<p style='font-size:16px;'><strong>Utöka sökområde yrkesmässigt</strong></p>",
                unsafe_allow_html=True,
                help="Utöka sökområde yrkesmässigt genom att välja yrkesbenämningar i listan ned. Sökområdet uttökas med yrkesgruppen som yrkesbenämningen tillhör."
            )

            for s in st.session_state.selectable_similar:
                e, f = st.columns([3, 1])
                string_similar, occupation_group_id = create_string_similar(s)
                e.markdown(string_similar, unsafe_allow_html=True)

                selected = f.checkbox(
                    occupation_group_id,
                    key=occupation_group_id,
                    value=occupation_group_id in st.session_state.included_groups,
                    label_visibility="collapsed"
                )

                if selected and occupation_group_id not in st.session_state.included_groups:
                    st.session_state.included_groups.append(occupation_group_id)
                    name = st.session_state.occupation_group_id_name.get(occupation_group_id)
                    st.session_state.included_group_names.append(name)
                    st.rerun()
                elif not selected and occupation_group_id in st.session_state.included_groups:
                    st.session_state.included_groups.remove(occupation_group_id)
                    name = st.session_state.occupation_group_id_name.get(occupation_group_id)
                    if name in st.session_state.included_group_names:
                        st.session_state.included_group_names.remove(name)
                    st.rerun()
        else:
            st.markdown("<p style='font-size:16px;'><strong>Inte tillräckligt med data för att kunna visa närliggande yrken</strong></p>", unsafe_allow_html=True)

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

    st.session_state.ssyk_code_selected = occupation_group[0:4]

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
    
    # Töm inkluderade kommuner om ort ändras
    if "previous_selected_location" in st.session_state:
        if st.session_state.previous_selected_location != selected_location:
            st.session_state.included_municipalities = []
    else:
        st.session_state.included_municipalities = []

    st.session_state.previous_selected_location = selected_location

    if selected_location:
        if 'included_groups' not in st.session_state:
            st.session_state.included_groups = []

        if 'included_group_names' not in st.session_state:
            st.session_state.included_group_names = []

        if 'included_municipalities' not in st.session_state:
            st.session_state.included_municipalities = []

        st.session_state.id_selected_location = st.session_state.locations_id.get(selected_location)
        selected_municipality_id, town_with_municipality, municipality_name = split_town_municipality(st.session_state.id_selected_location)

        if not occupation_group_id in st.session_state.included_groups:
            st.session_state.included_groups.append(occupation_group_id)
        if not occupation_group in st.session_state.included_group_names:
            st.session_state.included_group_names.append(occupation_group)
        if not selected_municipality_id in st.session_state.included_municipalities:
            st.session_state.included_municipalities.append(selected_municipality_id)

        st.session_state.selected_location_id = []
        st.session_state.selected_occupation_id = []

        st.session_state.locations_with_ads = create_locations_with_ads(st.session_state.id_selected_location)
        st.session_state.data_selected_location = st.session_state.locations_with_ads[0]

        st.session_state.relevant_locations_with_ads = st.session_state.locations_with_ads[1:]

        if st.session_state.similar:
            st.session_state.selectable_similar = create_selectable_similar(st.session_state.id_selected_location)
       
        update_location_ads_based_on_selection()

        show_options()

        with st.sidebar:
            a, b, c = st.columns(3)

            string_selected_location = create_string_location(st.session_state.data_selected_location)
            st.markdown(string_selected_location, unsafe_allow_html = True)

            st.session_state.all_ads_now, st.session_state.all_ads_historical = count_total_ad_numbers()

            skillnad_nu = st.session_state.all_ads_now - st.session_state.data_selected_location['ads'][0]
            skillnad_historiska = st.session_state.all_ads_historical - st.session_state.data_selected_location['ads'][1]

            a.metric(label = "Nu", value = st.session_state.all_ads_now, delta = skillnad_nu, help = "Antal annonser i Platsbanken för aktuell yrkesgrupp och inkluderade kommuner. Siffran nedanför är antalet annonser i inkluderade närliggande kommuner.")
            b.metric(label = "2024", value = st.session_state.all_ads_historical, delta = skillnad_historiska, help = "Antal annonser 2024 för aktuell yrkesgrupp och inkluderade kommuner. Siffran nedanför är antalet annonser i inkluderade närliggande kommuner.")

            muncipality_names = []
            for m in st.session_state.included_municipalities:
                muncipality_names.append(st.session_state.municipality_id_namn.get(m))
            muncipality_names = sorted(muncipality_names)
            muncipality_string = "<br />&emsp;&emsp;&emsp;".join(muncipality_names)
            string_to_print = f"<p style='font-size:16px;'><strong>Inkluderade kommuner</strong><br />&emsp;&emsp;&emsp;<small>{muncipality_string}</small></p>"
            st.markdown(string_to_print, unsafe_allow_html = True)

            occupation_group_names = []
            for g in st.session_state.included_group_names:
                occupation_group_names.append(g)
            occupation_group_names = sorted(occupation_group_names)
            occupation_string = "<br />&emsp;&emsp;&emsp;".join(occupation_group_names)
            string_to_print = f"<p style='font-size:16px;'><strong>Inkluderade yrkesgrupper</strong><br />&emsp;&emsp;&emsp;<small>{occupation_string}</small></p>"
            st.markdown(string_to_print, unsafe_allow_html = True)

            string_all = create_string_all_selected()
            st.markdown(string_all, unsafe_allow_html = True)

            restart_string = f"<p style='font-size:16px;'><strong>För att rensa din val</strong><br />COMMAND + R</p>"
            st.markdown(restart_string, unsafe_allow_html = True)

        text_dataunderlag_närliggande_orter = "<strong>Dataunderlag</strong><br />Annonsplaneraren baseras på avstånd mellan orter från öppen geodata, annonser i Platsbanken och Historiska berikade annonser knutna till aktuell yrkesgrupp och kommun."

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
        # Töm val om yrke har ändrats
        if "previous_selected_occupation" in st.session_state:
            if st.session_state.previous_selected_occupation != selected_occupation_name:
                st.session_state.included_municipalities = []
                st.session_state.included_groups = []
                st.session_state.included_group_names = []
        else:
            st.session_state.included_municipalities = []
            st.session_state.included_groups = []
            st.session_state.included_group_names = []

        st.session_state.previous_selected_occupation = selected_occupation_name

        id_selected_occupation = st.session_state.valid_occupations.get(selected_occupation_name)
        post_selected_occupation(id_selected_occupation)


def main ():
    initiate_session_state()
    fetch_data()
    choose_occupation_name()

if __name__ == '__main__':
    main ()