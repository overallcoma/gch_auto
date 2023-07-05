import configparser
import requests
import json
import html
import time
import datetime
import re

try:
    configfilename = "./gch2.cfg"
    gch_config = configparser.ConfigParser()
except Exception as e:
    print("Unable to load config file - please verify it exists")
    print(e)
    exit(1)

try:
    gch_config.read(configfilename)
except Exception as e:
    print("Unable to read config file")
    print(e)
    exit(1)


gch_config.event_id = (gch_config["target-config"])["event-id"]
gch_config.owner_id = (gch_config["target-config"])["owner-id"]
gch_config.entrytoken = (gch_config["account-config"])["entry-token"]
gch_config.check_frequency = int((gch_config["account-config"])["check-frequency"])
gch_config.search_start = (gch_config["search-filters"])["search-start"]
gch_config.search_end = (gch_config["search-filters"])["search-end"]
gch_config.filter_search_skywalk = bool(gch_config["search-filters"]["search-skywalk"])
gch_config.filter_search_blocks = bool(gch_config["search-filters"]["search-blocks"])
gch_config.filter_search_blocks_max = int(gch_config["search-filters"]["max-blocks"])
gch_config.filter_search_miles = bool(gch_config["search-filters"]["search-miles"])
gch_config.filter_search_miles_max = int((gch_config["search-filters"])["max-miles"])
gch_config.filter_search_hotel_name_enabled = gch_config.getboolean("search-filters", "hotel-name-filter-enabled")
gch_config.filter_search_hotel_name_string = (gch_config["search-filters"])["hotel-name-filter-keyword"]
gch_config.filter_search_room_keyword_enabled = gch_config.getboolean("search-filters", "hotel-room-filter-enabled")
gch_config.filter_search_room_keyword_include = (gch_config["search-filters"])["hotel-room-filter-filter-include"]
gch_config.filter_search_room_keyword_exclude = (gch_config["search-filters"])["hotel-room-filter-filter-exclude"]
gch_config.auto_book_enabled = (gch_config.getboolean("auto-book", "autobook-enabled"))




# Create a user agent string for requests in case they start blocking it again #
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
user_agent_header = {
    'User-Agent': user_agent
}


def passkey_parser(html_content):
    parsed_content = re.findall('<script id="last-search-results" type="application/json">(.*?)</script>',
                                html_content)[0]
    parsed_content = json.loads(parsed_content)
    return parsed_content


class hotelroom(object):
    name = ''
    distance = ''
    price = ''
    taxrate = ''
    taxcost = ''
    subtotal = ''
    inventory = 0
    roomtype = ''
    hotelID = ''
    roomID = ''

    def __init__(self, name, distance, price, taxrate, taxcost, subtotal, inventory, roomtype, hotelID, roomID):
        self.name = name
        self.distance = distance
        self.price = price
        self.taxrate = taxrate
        self.taxcost = taxcost
        self.subtotal = subtotal
        self.inventory = inventory
        self.roomtype = roomtype
        self.hotelID = hotelID
        self.roomID = roomID


def make_hotel_room_object(name, distance, price, taxrate, taxcost, subtotal, inventory, roomtype, hotelID, roomID):
    hotel_room = hotelroom(name, distance, price, taxrate, taxcost, subtotal, inventory, roomtype, hotelID, roomID)
    return hotel_room


def get_hotel_room_objects():
    base_portal_url = "https://book.passkey.com"
    housing_url_post_base = base_portal_url + "/event/" + gch_config.event_id + "/owner/" + gch_config.owner_id
    post_room_select_url = housing_url_post_base + "/rooms/select"
    housing_url_initial = base_portal_url + "/entry?token={}".format(gch_config.entrytoken)
    housing_url_available_post = housing_url_post_base + "/list/hotels/available"
    response = requests.get(housing_url_initial, headers=user_agent_header)
    response_cookies = response.cookies
    xsrf_token = response_cookies.get('XSRF-TOKEN')
    post_data = construct_search_post(xsrf_token)
    requests.post(housing_url_available_post, data='', headers=user_agent_header, cookies=response_cookies)
    response = requests.post(post_room_select_url, data=post_data, headers=user_agent_header, cookies=response_cookies)
    try:
        hotels = passkey_parser(response.text)
    except TypeError:
        current_time = str(datetime.datetime.now())
        print(current_time + " - Error Scraping Page - Continuing Script")
        print("This is an expected occasional error - do not worry")
        return []
    except Exception as i:
        current_time = str(datetime.datetime.now())
        print(current_time + " - Error Scraping Page - Continuing Script")
        print("This is not an expected error - report this for repair")
        print(i)
        return []

    available_room_list = []

    if hotels:
        for hotel in hotels:
            for block in hotel['blocks']:
                hotel_name = html.unescape(hotel['name'])
                if hotel['distanceUnit'] == 0:
                    distance = "Skywalk"
                elif hotel['distanceUnit'] == 1:
                    distance = "{} Block(s)".format(hotel['distanceFromEvent'])
                elif hotel['distanceUnit'] == 3:
                    distance = "{} Mile(s)".format(hotel['distanceFromEvent'])
                else:
                    distance = "unknown"
                hotel_room_price = sum(inv['rate'] for inv in block['inventory'])
                hotel_room_inventory = min(inv['available'] for inv in block['inventory'])
                hotel_room_type = html.unescape(block['name'])
                hotel_room_hotelID = (hotel['id'])
                hotel_room_roomID = (block['id'])

                try:
                    hotel_room_tax_policy = html.unescape(block['taxPolicy'])
                    hotel_room_tax_rate = float((hotel_room_tax_policy.split("%")[0])[-2:])
                except Exception as e:
                    hotel_room_tax_rate = 17
                    print(e)

                try:
                    hotel_total_tax_cost = (float(hotel_room_price) * float(hotel_room_tax_rate))/100
                except Exception as e:
                    hotel_total_tax_cost = 200
                    print(e)

                hotel_room_subtotal = str(format(float(float(hotel_room_price) + float(hotel_total_tax_cost)), '.2f'))
                hotel_room_price = str(format(hotel_room_price, '.2f'))
                hotel_room_tax_rate = str(format(hotel_room_tax_rate, '.2f'))
                hotel_total_tax_cost = str(format(hotel_total_tax_cost, '.2f'))

                hotel_room_object = make_hotel_room_object(hotel_name, distance, hotel_room_price, hotel_room_tax_rate, hotel_total_tax_cost, hotel_room_subtotal, hotel_room_inventory, hotel_room_type, hotel_room_hotelID, hotel_room_roomID)
                available_room_list.append(hotel_room_object)
    else:
        print("error parsing hotels through filters - aborting this run")
    return available_room_list


def construct_showavail_post():
    showavailable = True
    payload = {
        'showAvailable': showavailable
    }
    return payload


def construct_search_post(xsrf_token):
    search_hotel_id = 0
    search_block_id = 0
    search_numberofguests = 1
    search_numberofrooms = 1
    search_numberofchildren = 0
    payload = {
        'hotelId': search_hotel_id,
        '_csrf': xsrf_token,
        'blockMap.blocks[0].blockId': search_block_id,
        'blockMap.blocks[0].checkIn': gch_config.search_start,
        'blockMap.blocks[0].checkOut': gch_config.search_end,
        'blockMap.blocks[0].numberOfGuests': search_numberofguests,
        'blockMap.blocks[0].numberOfRooms': search_numberofrooms,
        'blockMap.blocks[0].numberOfChildren': search_numberofchildren
    }
    return payload


def filter_hotel_room_objects(hotel_room_object_list):

    # print("---------------INITIAL OBJECT LIST-----------------")
    # print(hotel_room_object_list)
    # print("---------------INITIAL OBJECT LIST-----------------")

    if hotel_room_object_list:
        hotel_room_object_list = filter_hotel_room_objects_distance(hotel_room_object_list)
    else:
        return hotel_room_object_list

    # print("---------------AFTER DISTANCE FILTER-----------------")
    # print(hotel_room_object_list)
    # print("---------------AFTER DISTANCE FILTER-----------------")

    if gch_config.filter_search_hotel_name_enabled:
        if hotel_room_object_list:
            hotel_room_object_list = filter_hotel_room_objects_hotelname(hotel_room_object_list)
        else:
            return hotel_room_object_list

    # print("---------------AFTER HOTEL NAME FILTER-----------------")
    # print(hotel_room_object_list)
    # print("---------------AFTER HOTEL NAME FILTER-----------------")

    if gch_config.filter_search_room_keyword_enabled:
        if hotel_room_object_list:
            hotel_room_object_list = filter_hotel_room_objects_roomkeyword(hotel_room_object_list)
        else:
            return hotel_room_object_list

    # print("---------------AFTER HOTEL ROOM FILTER-----------------")
    # print(hotel_room_object_list)
    # print("---------------AFTER HOTEL ROOM FILTER-----------------")


    # This is a sanity check to make sure rooms available exceeds 0
    # Sometimes setting the "only show available" fails, so this is here to avoid false positives
    return hotel_room_object_list


def filter_hotel_room_objects_distance(hotel_room_object_list):
    filtered_list = []
    for hotel_room in hotel_room_object_list:
        if gch_config.filter_search_skywalk:
            if "Skywalk" in hotel_room.distance:
                filtered_list.append(hotel_room)
        if gch_config.filter_search_blocks:
            if "Blocks" in hotel_room.distance:
                block_distance = str(hotel_room["distanceFromEvent"]).split(" ")[0]
                block_distance = int(block_distance)
                if float(block_distance) < float(gch_config.filter_search_blocks_max):
                    filtered_list.append(hotel_room)
        if gch_config.filter_search_miles:
            if "Mile(s)" in hotel_room.distance:
                miles_distance = hotel_room.distance.split(" ")[0]
                if float(miles_distance) < float(gch_config.filter_search_miles_max):
                    filtered_list.append(hotel_room)
    return filtered_list


def filter_hotel_room_objects_hotelname(hotel_room_object_list):
    filtered_list = []
    for hotel_room in hotel_room_object_list:
        if str(gch_config.filter_search_hotel_name_string) in str(hotel_room.name):
            filtered_list.append(hotel_room)
    return filtered_list


def filter_hotel_room_objects_roomkeyword(hotel_room_object_list):
    filtered_list = []
    for hotel_room in hotel_room_object_list:
        if gch_config.filter_search_room_keyword_include in hotel_room.name:
            if gch_config.filter_search_room_keyword_exclude not in hotel_room.roomtype:
                filtered_list.append(hotel_room)
    return filtered_list


def filter_hotel_room_objects_availablecheck(hotel_room_object_list):
    filtered_list = []
    for hotel_room in hotel_room_object_list:
        if hotel_room.inventory > 0:
            filtered_list.append(hotel_room)
    return filtered_list


def autobook_room(hotel_room):
    print("Auto-Book Is Being Attempted")
    session = requests.session()

    base_portal_url = "https://book.passkey.com"
    housing_url_initial = base_portal_url + "/event/" + gch_config.event_id + "/owner/" + gch_config.owner_id
    housing_url_post_base = base_portal_url + "/event/" + gch_config.event_id + "/owner/" + gch_config.owner_id
    housing_url_available_post = housing_url_post_base + "/list/hotels/available"

    session.get(housing_url_initial, headers=user_agent_header)
    try:
        post_room_select_url = housing_url_post_base + "/rooms/select"
        post_data = construct_search_post()
        session.post(post_room_select_url, data=post_data, headers=user_agent_header)
    except Exception as e:
        print("Could not configure the autobook - initial session configuration")
        print(e)
    try:
        post_hotel_select_url = housing_url_post_base + "/rooms/select/update"
        hotel_select_json = autobook_hotel_select_encode(hotel_room)
        session.post(post_hotel_select_url, json=hotel_select_json, headers=user_agent_header)
    except Exception as e:
        print("Could not excecute autobook - update hotel selection")
        print(e)
    try:
        post_room_select_url = housing_url_post_base + "/rooms/select/update?updateTotals=false"
        room_select_json = autobook_room_select_encode(hotel_room)
        session.post(post_room_select_url, json=room_select_json, headers=user_agent_header)
    except Exception as e:
        print("Could not execute autobook - update room selection")
        print(e)
    try:
        get_guest_info_url = housing_url_post_base + "/guest/info"
        csrf_token_collection = session.get(get_guest_info_url)
        # Fuck you guys and your shitty security
        csrf_token = (re.search('name="_csrf" value="(.*)" />', csrf_token_collection.text).group(1))
        print("Your CSRF Token is " + csrf_token)
    except Exception as e:
        print("Could not execute autobook - update guest info")
        print(e)
    try:
        guest_info_update_url = housing_url_post_base + "/guest/info"
        guest_info_postdata = autobook_guestinfo_construct(hotel_room, csrf_token)
        session.post(guest_info_update_url, data=guest_info_postdata, headers=user_agent_header)
    except Exception as e:
        print("Could not execute autobook - update guest info")
        print(e)
    try:
        guest_payment_url = housing_url_post_base + "/guest/payment"
        guest_payment_postdata = autobook_payment_post_construct(csrf_token)
        session.post(guest_payment_url, data=guest_payment_postdata, headers=user_agent_header)
    except Exception as e:
        print("Could not execute autobook - payment update")
        print(e)
    try:
        guest_reservation_save_url = housing_url_post_base + "/reservation/save"
        guest_reservation_postdata = autobook_reservation_post_construct(csrf_token)
        session.post(guest_reservation_save_url, data=guest_reservation_postdata, headers=user_agent_header)
    except Exception as e:
        print("Could not execute autobook - accept reservation terms")
        print(e)
    print("Auto-Book has completed")


def autobook_hotel_select_encode(hotel_room):
    hotel_select_data = {
                    "hotelId": str(hotel_room.hotelID),
                    "distanceEnd": 0,
                    "maxGuests": 4,
                    "blockMap": {
                        "blocks": [{
                            "blockId": 0,
                            "checkIn": gch_config.search_start,
                            "checkOut": gch_config.search_end,
                            "numberOfGuests": 1,
                            "numberOfRooms": 1,
                            "numberOfChildren": 0
                        }],
                        "totalRooms": 1,
                        "totalGuests": 1
                    },
                    "minSlideRate": 0,
                    "maxSlideRate": 0,
                    "wlSearch": False,
                    "showAll": False,
                    "mod": False
    }
    return hotel_select_data


def autobook_room_select_encode(hotel_room):
    room_select_data = {"hotelId": str(hotel_room.hotelID),
                        "distanceEnd": 0,
                        "maxGuests": 4,
                        "blockMap": {
                            "blocks": [{
                                "blockId": 0,
                                "checkIn": gch_config.search_start,
                                "checkOut": gch_config.search_end,
                                "numberOfGuests": 1,
                                "numberOfRooms": 1,
                                "numberOfChildren": 0
                            },
                                {"blockId": str(hotel_room.roomID),
                                 "checkIn": gch_config.search_start,
                                 "checkOut": gch_config.search_end,
                                 "numberOfRooms": 1,
                                 "numberOfGuests": 1,
                                 "numberOfChildren": 0}],
                            "totalRooms": 1,
                            "totalGuests": 1},
                        "minSlideRate": 0,
                        "maxSlideRate": 0,
                        "wlSearch": False,
                        "showAll": False,
                        "mod": False}
    return room_select_data


def autobook_guestinfo_construct(hotel_object, csrf_token):
    autobook_guestinfo = gch_config["auto-book"]
    guest_firstname = autobook_guestinfo["guest-firstname"]
    guest_lastname = autobook_guestinfo["guest-lastname"]
    guest_email = autobook_guestinfo["guest-email"]
    guest_country = autobook_guestinfo["guest-country"]
    guest_streetaddress = autobook_guestinfo["guest-streetaddress"]
    guest_city = autobook_guestinfo["guest-city"]
    guest_state = autobook_guestinfo["guest-state"]
    guest_zip = autobook_guestinfo["guest-zip"]
    guest_phone = autobook_guestinfo["guest-phone"]
    guest_checkin = autobook_reformat_date(gch_config.search_start)
    guest_checkout = autobook_reformat_date(gch_config.search_end)
    payload = {
        'numberofadults': 1,
        'numberofchildren': 0,
        '_guestWithSameName': 'on',
        'reservations[0].ackNumber': '',
        'reservations[0].id': 0,
        'reservations[0].blockId': hotel_object.roomID,
        'reservations[0].checkInDate': guest_checkin,
        'reservations[0].checkOutDate': guest_checkout,
        'reservations[0].eventId': 50023680,
        'reservations[0].groupTypeId': 217764954,
        'reservations[0].hotelId': hotel_object.hotelID,
        'reservations[0].statusId': 0,
        'reservations[0].charge': str(hotel_object.price),
        'reservations[0].taxAmount': str(hotel_object.taxcost),
        'reservations[0].subtotal': str(hotel_object.subtotal),
        'reservations[0].guests[0].id': 0,
        'reservations[0].guests[0].arrDate': guest_checkin,
        'reservations[0].guests[0].prefix': ' ',
        'reservations[0].guests[0].firstName': guest_firstname,
        'reservations[0].guests[0].middleName': ' ',
        'reservations[0].guests[0].lastName': guest_lastname,
        'reservations[0].guests[0].suffix': ' ',
        'reservations[0].guests[0].position': ' ',
        'reservations[0].guests[0].familyName': '',
        'reservations[0].guests[0].givenName': '',
        'reservations[0].guests[0].depDate': guest_checkout,
        'reservations[0].guests[0].email': guest_email,
        'reservations[0].guests[0].confirmEmail': guest_email,
        'reservations[0].guests[0].organization': ' ',
        'reservations[0].guests[0].address.country.alpha2Code': guest_country,
        'reservations[0].guests[0].address.address1': guest_streetaddress,
        'reservations[0].guests[0].address.address2': ' ',
        'reservations[0].guests[0].address.city': guest_city,
        'reservations[0].guests[0].address.state': guest_state,
        'reservations[0].guests[0].address.zip': guest_zip,
        'reservations[0].guests[0].phoneNumber': guest_phone,
        'reservations0.maxTabindex': 4,
        '_reservations[0].accessibilityRequested': 'on',
        'reservations[0].smokingPreference.id': 2,
        'reservations[0].guests[0].specialRequests': '',
        'reservations[0].specialRequests': '',
        '_reservations[0].optIn': 'on',
        '_csrf': csrf_token
     }
    return payload


def autobook_payment_post_construct(csrf_token):
    autobook_guestinfo = gch_config["auto-book"]
    guest_country = autobook_guestinfo["guest-country"]
    guest_streetaddress = autobook_guestinfo["guest-streetaddress"]
    guest_city = autobook_guestinfo["guest-city"]
    guest_state = autobook_guestinfo["guest-state"]
    guest_zip = autobook_guestinfo["guest-zip"]
    guest_phone = autobook_guestinfo["guest-phone"]
    guest_creditcardtype = str(autobook_guestinfo["guest-creditcardtype"])
    guest_checkout = autobook_reformat_date(gch_config.search_end)
    guest_creditcard = str(autobook_guestinfo["guest-creditcard"])
    guest_creditcardexpiryyear = str(autobook_guestinfo["guest-creditcardexpiryyear"])
    guest_creditcardexpirymonth = str(autobook_guestinfo["guest-creditcardexpirymonth"])
    guest_creditcardholdername = autobook_guestinfo["guest-creditcardholdername"]
    payload = {
        'billingInfo[0].payment.paymentType': 'CCPayment',
        'billingInfo[0].payment.otherPayment.otherPayNote': 'No Comment',
        'billingInfo[0].payment.creditCard.cardTypeId': guest_creditcardtype,
        'billingInfo[0].payment.creditCard.depDate': guest_checkout,
        'billingInfo[0].payment.creditCard.cardNumber': guest_creditcard,
        'billingInfo[0].payment.creditCard.expiryMonth': guest_creditcardexpirymonth,
        'billingInfo[0].payment.creditCard.expiryYear': guest_creditcardexpiryyear,
        'billingInfo[0].payer.holderName': guest_creditcardholdername,
        'billingInfo[0].payer.phoneNumber': guest_phone,
        'billingInfo[0].payer.address.address1': guest_streetaddress,
        'billingInfo[0].payer.address.address2': ' ',
        'billingInfo[0].payer.address.city': guest_city,
        'billingInfo[0].payer.address.country.alpha2Code': guest_country,
        'billingInfo[0].payer.address.state': guest_state,
        'billingInfo[0].payer.address.zip': guest_zip,
        'splitFolio[0]': 101,
        '_csrf': csrf_token
    }
    return payload


def autobook_reservation_post_construct(csrf_token):
    payload = {
        'attendeeConsentAgreements[0].consentGiven': 1,
        '_attendeeConsentAgreements[0].consentGiven': 'on',
        '_csrf': csrf_token
    }
    return payload


def autobook_reformat_date(timestring):
    time_array = timestring.split("-")
    year = str(int(time_array[0]))
    year = year[-2:]
    month = str(int(time_array[1]))
    day = str(int(time_array[2]))
    reformatted_date = month + "/" + day + "/" + year
    return reformatted_date


def search_workflow():
    hotel_room_objects = get_hotel_room_objects()
    hotel_room_objects_filtered = filter_hotel_room_objects(hotel_room_objects)
    autobook_wasrun = 0
    if hotel_room_objects_filtered:
        print("\nValid hotels based on search filters found:\n")
        for hotels in hotel_room_objects_filtered:
            print(hotels.name)
        if gch_config.auto_book_enabled == True:
            try:
                print("starting auto-book")
                print(hotel_room_objects_filtered[0].name)
                autobook_room(hotel_room_objects_filtered[0])
                print("AutoBook Attempted")
                autobook_wasrun = 1
            except Exception as i:
                print("AutoBook Failed")
                print(i)
    print("Search completed " + str(datetime.datetime.now()))
    if autobook_wasrun == 0:
        return 1
    if autobook_wasrun == 1:
        return 0
    return 0


print("Gencon-Hotels-2 is running")
while True:
    kill_check = search_workflow()
    if kill_check == 1:
        time.sleep(gch_config.check_frequency)
    elif kill_check == 0:
        exit(1)
