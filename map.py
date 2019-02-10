import folium
import re
from geopy.geocoders import Nominatim
import geopy.exc


def define_year(name):
    """
    (str) -> str

    Reads the year in which the movie was filmed

    :param name: the name of the film

    :return:
    (str) the year in which given movie was filmed
    """
    lindex = name.find('(') + 1
    year = "????"

    while lindex != 0:
        try:
            if name[lindex] == '+':
                raise ValueError
            rindex = name.find(')', lindex)

            if rindex == -1:
                return year
            int(name[lindex:rindex])
            if len(name[lindex:rindex]) < 4:
                raise ValueError

            year = name[lindex:rindex]
            break
        except ValueError:
            lindex = name.find('(', lindex) + 1

    if year == '????':
        try:
            index = name.find('(') + 1
            int(name[index: index + 4])
            return name[index: index + 4]
        except ValueError:
            pass
    return year


def define_country(location):
    """
    (str) -> str

    Reads the name of country in which the movie was filmed

    :param location:  the place where movie was filmed

    :return:
    (str) the name of a country
    """
    return location[location.rfind(',') + 1:].strip()


def define_coords(location):
    """
    (str) -> tuple

    Generate coordinates for given location

    :param location: the place where movie was filmed

    :return:
    (tuple) coordinates
    """
    try:
        result = geolocator.geocode(location, timeout=500000)
        if result:
            return result.latitude, result.longitude
        else:
            result = geolocator.geocode(location[location.find(',') + 1:],
                                        timeout=500000)
            if result:
                return result.latitude, result.longitude
    except geopy.exc.GeopyError as error:
        print(error)


def read_File(file, movie_by_year):
    """
    (str, dict) -> None

    :param file: the name of dataset
    :param movie_by_year: dictionary of the films sorted by years

    :return: None
    """
    f = open(file, 'r', encoding='latin1')

    # switch to necessary line
    line = f.readline()
    while True:
        if line.startswith('LOCATIONS LIST'):
            f.readline()
            break
        line = f.readline()

    for i in f.readlines():
        if i.startswith('------------------------------------------'):
            break
        row = re.sub('\t+', '\t', i).split('\t')
        location = row[1][:-1 if row[1][-1] == '\n' else None]
        year = define_year(row[0])

        # check whether year was correctly defined (since in dataset
        # could be sth like (????) instead of year)
        if year == '????':
            continue

        country = define_country(location)
        if country not in movie_by_year[year]:
            movie_by_year[year][country] = {'films': [],
                                            'count': 0}
        movie_by_year[year][country]['films'].append((row[0], location))
        movie_by_year[year][country]['count'] += 1


def define_color(country, dct, maximum):
    """
    (dict dict, int) -> dict

    Generate a color for the country (it gets by playing with red and green)

    :param country: dictionary of some info about the country
    :param dct: dictionary of the movies sorted by countries
    :param maximum: maximum amount of movies filmed in 1 country

    :return:
    (dict) {'fillColor' - color in which we want to color country
            'fillOpacity' - opacity of that color}
    """
    if country['NAME'] in dct:
        name = country['NAME']
    elif country['ISO2'] in dct:
        name = country['ISO2']
    elif country['ISO3'] in dct:
        name = country['ISO3']
    else:
        name = country['FIPS']

    if name not in dct:
        return {'fillColor': '#fff'}

    count = dct[name]['count']
    k = 255 / maximum

    red = hex(int(k * count))[2:]
    if len(red) == 1:
        red = '0' + red
    green = hex(int(k * (maximum - count)))[2:]
    if len(green) == 1:
        green = '0' + green
    return {'fillColor': '#' + red + green + '00',
            'fillOpacity': 0.7}


def create_Markers(fg_markers, movie_by_year, year, limit, maximum):
    """
    (folium.map.FeatureGroup object, dict, int) -> None

    Create Markers for movies filmed in chosen year (limited by the limit)

    :param fg_markers: folium group of Countries
    :param movie_by_year: dictionary of the films sorted by years
    :param year: the year for which the user want to get the Map
    :param limit: limit for markers the user want to see on the Map

    :return: None
    """
    i = 0
    try:
        # check whether the services throw error 429
        geolocator.geocode('USA')

        for index in range(maximum + 1):
            for country in movie_by_year[year]:
                films = movie_by_year[year][country]['films']
                if len(films) <= index:
                    continue
                film = movie_by_year[year][country]['films'][index]
                coords = define_coords(film[1])
                if coords is None:
                    continue
                i += 1
                print(i, 'marker')
                if i == limit:
                    raise geopy.exc.GeopyError
                fg_markers.add_child(folium.Marker(location=coords,
                                                   popup=film[0] + film[1],
                                                   icon=folium.Icon()))
    except geopy.exc.GeopyError as error:
        print(error)


def color_Contries(fg_countries, movie_by_year, year, maximum):
    """
    (folium.map.FeatureGroup object, dict, int) -> None

    Create border for the entire countries and fill them with colors
    (based on the amount of movies filmed in chosen year)

    :param fg_countries: folium group of Countries
    :param movie_by_year: dictionary of the films sorted by years
    :param year: the year for which the user want to get the Map

    :return: None
    """


    file_world = open('world.json', 'r', encoding='utf-8-sig').read()
    style_lambda = lambda country: define_color(country['properties'],
                                                movie_by_year[year],
                                                maximum)
    fg_countries.add_child(folium.GeoJson(data=file_world,
                                          style_function=style_lambda))


def create_Map(out_file, year, limit, movie_by_year):
    """
    (str, int, int, dict) -> None

    Generates the Map with 3 layers (basic map, marker, countries)

    :param out_file: the name of the Map the user want to create
    :param year: the year for which the user want to get the Map
    :param limit: limit for markers the user want to see on the Map
    :param movie_by_year: dictionary of the films sorted by years

    :return: None
    """
    # create Map
    map = folium.Map()

    # count maximum amount of movies filmed in chosen year
    maximum = max(movie_by_year[year],
                  key=lambda country: movie_by_year[year][country]['count'])
    maximum = movie_by_year[year][define_country(maximum)]['count']

    # set Markers on the Map
    fg_markers = folium.FeatureGroup(name="Markers")
    create_Markers(fg_markers, movie_by_year, year, limit, maximum)

    # fill countries on the Map with colors
    fg_countries = folium.FeatureGroup(name="Countries")
    color_Contries(fg_countries, movie_by_year, year, maximum)

    # add layers on the Map
    map.add_child(fg_markers)
    map.add_child(fg_countries)
    map.add_child(folium.LayerControl())

    # create HTML Map
    map.save(out_file)


def read_year(dct):
    """
    (dict) -> int

    Ask user to set the year for which the user want to create a Map

    :param dct: dictionary of the films sorted by years

    :return:
    (int) year for which the user want to create a Map
    """
    msg = 'Please, write a year for which you want to get map (1870 - 2030): '
    while True:
        try:
            year = input(msg).strip()
            int(year)
            if year not in dct:
                print("Sorry, but in this year wasn't filmed any movie")
                continue
            else:
                return year
        except ValueError:
            print("PLease, check whether you correctly mentioned the year")


def read_limit():
    """
    (None) -> int

    Ask user to set the limit for markers he want to see on the Map

    :return:
    (int) limit
    """
    while True:
        try:
            msg = 'Please, write an amount of films for which you want to '
            limit = input(msg + 'create a map (default: 20): ')
            return int(limit) if limit else 20
        except ValueError:
            err_msg = 'PLease, check whether you correctly mentioned '
            print(err_msg + 'the limit you want to set')


if __name__ == '__main__':
    # create geolocator
    geolocator = Nominatim()

    # create the dictionary where will be saved data from dataset
    movie_by_year = {str(i): dict() for i in range(1870, 2030)}

    # ask user
    year = read_year(movie_by_year)
    limit = read_limit()

    # read dataset
    read_File('locations.list', movie_by_year)

    # write a Map
    create_Map('Map.html', year, limit, movie_by_year)
