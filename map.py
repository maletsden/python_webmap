import time
import folium
import re
from geopy.geocoders import Nominatim
import geopy.exc


# t = time.time()
# print(time.time() - t)
# print(data)

# map = folium.Map(location=[48.314775, 25.082925])


def define_year(name):
    index = name.find('(') + 1
    return name[index: index + 4]


def define_country(location):
    return location[location.rfind(',') + 1:].strip()


def define_coords(location):
    print(location)
    result = geolocator.geocode(location, timeout=500000)
    if result:
        return result.latitude, result.longitude
    # elif '-' in location:
    #     result = geolocator.geocode(location.split('-')[-1], timeout=500000)
    #     return result.latitude, result.longitude if result else None
    else:
        result = geolocator.geocode(location[location.find(',') + 1:], timeout=500000)
        if result:
            return result.latitude, result.longitude

def read_File(file, movie_by_year):
    f = open(file)

    for i in f.readlines():
        # check += 1
        row = re.sub('\t+', '\t', i).split('\t')
        location = row[1][:-1 if row[1][-1] == '\n' else None]
        year = define_year(row[0])

        # check whether year was correctly defined (since in dataset could be sth like (????) instead of year)
        try:
            int(year)
        except ValueError:
            continue

        country = define_country(location)
        if country not in movie_by_year[year]:
            movie_by_year[year][country] = {'films': [], 'count': 0}
        movie_by_year[year][country]['films'].append((row[0], location))
        movie_by_year[year][country]['count'] += 1


def define_color(country, dct, maximum):
    if country not in dct:
        return 'rgba(0, 0, 0, 0)'
    count = dct[country]['count']
    k = 255 / maximum
    red = str(k * count)
    green = str(k * (maximum - count))
    return 'rgb(' + red + ',' + green + ', 0)'



def create_Map(out_file, year, limit, movie_by_year):
    i = 0

    map = folium.Map()
    fg_markers = folium.FeatureGroup(name="Markers")
    try:
        for country in movie_by_year[year]:
            for film in movie_by_year[year][country]['films']:
                coords = define_coords(film[1])
                if coords is None:
                    continue
                i += 1
                if i == limit:
                    raise geopy.exc.GeopyError
                print(i)
                fg_markers.add_child(folium.Marker(location=coords,
                                            popup=film[0],
                                            icon=folium.Icon()))
    except geopy.exc.GeopyError as error:
        print(error)




    maximum = max(movie_by_year[year], key=lambda country: movie_by_year[year][country]['count'])
    maximum = movie_by_year[year][define_country(maximum)]['count']
    print(maximum)
    fg_countries = folium.FeatureGroup(name="Countries")

    # print(movie_by_year[year])

    file_world = open('world.json', 'r', encoding='utf-8-sig').read()
    fg_countries.add_child(folium.GeoJson(data=file_world,
                                          style_function=lambda country: {'fillColor': define_color(country['properties']['NAME'],
                                                                                                    movie_by_year[year],
                                                                                                    maximum)}))

    map.add_child(fg_markers)
    map.add_child(fg_countries)
    map.add_child(folium.LayerControl())

    map.save(out_file)

def read_year(dct):
    while True:
        try:
            year = input("Please, write a year for which you want to get a map (1947 - 2021): ")
            int(year)
            if year not in dct:
                print("Sorry, but in this year wasn't filmed any movie")
                continue
            else:
                return year
        except ValueError:
            print("PLease, check whether you correctly mentioned the year")


def read_limit():
    while True:
        try:
            limit = input("Please, write an amount of films for which you want to create a map (default: 100): ")
            return int(limit) if limit else 100
        except ValueError:
            print("PLease, check whether you correctly mentioned the limit you want to set")

if __name__ == '__main__':
    geolocator = Nominatim()
    movie_by_year = {str(i): dict() for i in range(1947, 2021)}

    read_File('loca.list', movie_by_year)
    # year = read_year(movie_by_year)
    # year = input("Please, write a year for which you want to get a map: ")

    # limit = read_limit()
    year = '2008'
    limit = 10
    print(limit)
    create_Map('Map.html', year, limit, movie_by_year)