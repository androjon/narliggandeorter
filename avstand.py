import streamlit as st
import json
import math

@st.cache_data
def import_data(filename):
    with open(filename) as file:
        content = file.read()
    output = json.loads(content)
    return output

def create_ads_occupations(id_occupation, id_selected_location, selected_location):
    other_locations = st.session_state.geodata.get(id_selected_location)

    all_locations = {}
    all_locations[id_selected_location] = 0
    for l, d in other_locations.items():
        location_name = st.session_state.id_locations.get(l)
        if location_name:
            all_locations[l] = d

    all_occupations = [id_occupation]
    for value in st.session_state.similar.values():
        all_occupations.append(value[0])

    all_ads = st.session_state_ad_data
    ads_occupations = {}
    for o in all_occupations:
        ads_o = {}
        all_ads_o = all_ads.get(o)
        for l, d in all_locations.items():
            if l == id_selected_location:
                ads_selected = all_ads_o.get(l)
                if not ads_selected:
                    ads_selected = [0, 0]
                ads_o[id_selected_location] = {
                    "ortnamn": selected_location,
                    "annonser": [ads_selected[0], ads_selected[1]],
                    "avstånd": d}
            else:
                ads_location = all_ads_o.get(l)
                if ads_location:
                    location_name = st.session_state.id_locations.get(l)
                    if location_name:
                        ads_o[l] = {
                            "ortnamn": location_name,
                            "annonser": [ads_location[0], ads_location[1]],
                            "avstånd": d}
        ads_occupations[o] = ads_o
    return all_locations, ads_occupations

def fetch_data():
    st.session_state.occupationdata = import_data("valid_occupations_with_info_v25.json")
    for key, value in st.session_state.occupationdata.items():
        st.session_state.valid_occupations[value["preferred_label"]] = key
    st.session_state.locations_id = import_data("ortnamn_id.json")
    st.session_state.id_locations = import_data("id_ortnamn.json")
    st.session_state.valid_locations = list(st.session_state.locations_id.keys())
    st.session_state.geodata = import_data("tatorter_distance.json")
    st.session_state_ad_data = import_data("yb_ort_annonser_nu_2024.json")

def show_initial_information():
    st.logo("af-logotyp-rgb-540px.jpg")
    st.title("Närliggande orter")
    initial_text = "Ett försöka att erbjuda information/stöd för arbetsförmedlare när det kommer till GYR-Y (Geografisk och yrkesmässig rörlighet - Yrke). Informationen är taxonomi- och annonsdriven och berör 1140 yrkesbenämningar. Det är dessa yrkesbenämningar som bedöms ha tillräckligt annonsunderlag för pålitliga beräkningar."
    st.markdown(f"<p style='font-size:12px;'>{initial_text}</p>", unsafe_allow_html=True)

def initiate_session_state():
    if "valid_occupations" not in st.session_state:
        st.session_state.valid_occupations = {}
        st.session_state.adwords_occupation = {}
        st.session_state.similar = None
        st.session_state.selected_similar = []

def create_tree(field, group, occupation, barometer, bold):
    SHORT_ELBOW = "└─"
    SPACE_PREFIX = "&nbsp;&nbsp;&nbsp;&nbsp;"
    LONG_PREFIX = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    strings = [f"{field}"]
    if barometer:
        barometer_name = barometer[0]
        if bold == "barometer":
            barometer_name = f"<strong>{barometer_name}</strong>"
    if bold == "occupation":
        occupation = f"<strong>{occupation}</strong>"
    elif bold == "group":
        group = f"<strong>{group}</strong>"
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

def create_string_chosen_locations(data):
    strings = []
    for d in data:
        annonstext = f"Annonser {d[1]['annonser'][0]}({d[1]['annonser'][1]})"
        strings.append(f"{d[1]['ortnamn']}<br />&emsp;&emsp;&emsp;{annonstext}")
    string = "<br />".join(strings)
    location_string = f"<p style='font-size:16px;'>{string}</p>"
    return location_string

def create_string_locations(data):
    strings = []
    for d in data:
        annonstext = f"{d[1]['avstånd']} kilometer - Annonser {d[1]['annonser'][0]}({d[1]['annonser'][1]})"
        strings.append(f"{d[1]['ortnamn']}<br />&emsp;&emsp;&emsp;<small>{annonstext}</small>")
    string = "<br />".join(strings)
    location_string = f"<p style='font-size:16px;'>{string}</p>"
    return location_string

def update_selected():
    st.session_state.selected_similar = []

def show_selectable_similar(data):
    with st.sidebar:
        selection = {}
        for k, v in data.items():
            name = f"{v[0]} {v[1]}({v[2]})"
            selection[name] = k
        selected = st.pills("Välj en eller flera närliggande yrken", list(selection.keys()), selection_mode = "multi", on_change = update_selected)
        if selected:
            selected_ids = []
            for s in selected:
                selected_ids.append(selection.get(s))
            st.session_state.selected_similar = selected_ids

def post_selected_occupation(id_occupation):
    info = st.session_state.occupationdata.get(id_occupation)

    occupation_name = info["preferred_label"]
    occupation_group = info["occupation_group"]
    occupation_field = info["occupation_field"]
    try:
        barometer = [f"{info['barometer_name']} (yrkesbarometeryrke)", info["barometer_above_ssyk"], info["barometer_part_of_ssyk"]]
    except:
        barometer = None
    try:
        st.session_state.similar = info["similar_occupations"]
    except:
        st.session_state.similar = None


    field_string = f"{occupation_field} (yrkesområde)"
    group_string = f"{occupation_group} (yrkesgrupp)"
    occupation_string = f"{occupation_name} (yrkesbenämning)"
    if barometer:
        tree = create_tree(field_string, group_string, occupation_string, barometer, "occupation")
    else:
        tree = create_tree(field_string, group_string, occupation_string, None, "occupation")

    st.markdown(tree, unsafe_allow_html = True)

    valid_locations = sorted(st.session_state.valid_locations)
    selected_location = st.selectbox(
        "Välj en ort",
        (valid_locations), placeholder = "", index = None)

    if selected_location:
        id_selected_location = st.session_state.locations_id.get(selected_location)

        all_locations, ads_occupations = create_ads_occupations(id_occupation, id_selected_location, selected_location)

        col1, col2 = st.columns(2)

        with col2:
            a, b, c = st.columns(3)

        st.write("---")

        col3, col4 = st.columns(2)

        if st.session_state.similar:
            add_similar = st.toggle("Inkludera närliggande yrken")

            if add_similar:
                similiar_name_ads = {}
                for value in st.session_state.similar.values():
                    id_similar = value[0]
                    info_similar = st.session_state.occupationdata.get(id_similar)
                    name_similar = info_similar["preferred_label"]

                    total_ads_similar = [name_similar, 0, 0]
                    for l in all_locations.keys():
                        try:
                            ads_similar_location = ads_occupations[id_similar][l]["annonser"]
                            total_ads_similar[1] += ads_similar_location[0]
                            total_ads_similar[2] += ads_similar_location[1]
                        except:
                            pass
                    similiar_name_ads[id_similar] = total_ads_similar

                show_selectable_similar(similiar_name_ads)

        alla_nu = 0
        alla_historiskt = 0

        locations_with_ads_max = {}
        for l, d in all_locations.items():
            location_name = st.session_state.id_locations.get(l)
            try:
                ads_occupation_location = ads_occupations[id_occupation][l]["annonser"]
                locations_with_ads_max[l] = {
                                "ortnamn": location_name,
                                "annonser": [ads_occupation_location[0], ads_occupation_location[1]],
                                "avstånd": d}
                alla_nu += ads_occupation_location[0]
                alla_historiskt += ads_occupation_location[1]
            except:
                locations_with_ads_max[l] = {
                                "ortnamn": location_name,
                                "annonser": [0, 0],
                                "avstånd": d}

        if st.session_state.selected_similar:
            for s in st.session_state.selected_similar:
                for l, d in all_locations.items():
                    try:
                        ads_similar_location = ads_occupations[s][l]["annonser"]
                        locations_with_ads_max[l]["annonser"][0] += ads_similar_location[0]
                        locations_with_ads_max[l]["annonser"][1] += ads_similar_location[1]
                        alla_nu += ads_similar_location[0]
                        alla_historiskt += ads_similar_location[1]
                    except:
                        pass

        ads_grund = ads_occupations[id_occupation][id_selected_location]["annonser"]

        skillnad_nu = alla_nu - ads_grund[0]
        skillnad_historiska = alla_historiskt - ads_grund[1]

        a.metric(label = "Platsbanken", value = alla_nu, delta = skillnad_nu)
        b.metric(label = "2024", value = alla_historiskt, delta = skillnad_historiska)

        list_locations_with_ads_max = list(locations_with_ads_max.items())

        sökt_ort = list_locations_with_ads_max[0]
        andra_orter = list_locations_with_ads_max[1:]

        antal_orter = len(andra_orter)
        n = math.ceil(antal_orter / 2)

        locations_1 = andra_orter[:n]
        locations_2 = andra_orter[n:]

        geo_string1 = create_string_locations(locations_1)
        geo_string2 = create_string_locations(locations_2)

        with col1:
            st.write("")
            sökt_ort_string = create_string_chosen_locations([sökt_ort])
            st.markdown(sökt_ort_string, unsafe_allow_html = True)

            #Skriv ut sökt ort här med annonsanatal.
        
        

        with col3:
            st.markdown(geo_string1, unsafe_allow_html = True)

        with col4:
            st.markdown(geo_string2, unsafe_allow_html = True)

        text_dataunderlag_närliggande_orter = "<strong>Dataunderlag</strong><br />Närliggande orter baseras på avstånd mellan orter från öppen geodata, annonser i Platsbanken och Historiska berikade annonser knutna till dessa orter och vald yrkesbenämning."
        
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