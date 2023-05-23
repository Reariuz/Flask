''' module for calculating paths on geojson basis'''

import os
import itertools
import math
import geojson
from vincenty import vincenty_inverse




class ShortestPath():
    '''generate a Path based upon a geojson point obj'''

    def __init__(self,geojson_obj):

        try:
            geojson_obj.is_valid

        except AttributeError:
            print("hier sollte ne fehlermeldung stehen, obj ist nicht vom richtigen typ")


        geojson_obj.errors()
        self.geojson_obj = geojson_obj
        self.find_id_groups()
        self.multi_path()
        self.generate_path()

    # print our string object
    def __repr__(self):
        return 'Object: {}'.format(self.my_feature)

    @property
    def __geo_interface__(self):
        return self.my_feature

    def find_id_groups(self):
        part_list = []
        y = []
        a = 1
        for count in range(len(self.geojson_obj['features'])):
            if int(self.geojson_obj['features'][count]['properties']['group']) == a:
                part_list.append(int(self.geojson_obj['features'][count]['properties']['id']))
            else:
                a = int(self.geojson_obj['features'][count]['properties']['group'])
                y.append(part_list)
                part_list = []
                part_list.append(int(self.geojson_obj['features'][count]['properties']['id']))

        y.append(part_list)
        self.id_groups = y
        return 0





    #finds the path of a single group
    def __single_path(self,start_point,finishing_point,id_collection):
        
        if isinstance(id_collection,int) is True:
            return id_collection


        #function looks up a combination of two numbers a and b in a nested list(distance_matrix) and returns the float
        def _lookup(a,b,c):
            for row in c:
                if row[0][0] == a and row[0][1] == b:
                    return float(row[1])
                elif row[0][0] == b and row[0][1] == a:
                    return float(row[1])
                else:
                    continue


        # generate all combinations of 2 IDs exluding doubles when permutaded while using the IDs from the list
        id_combinations = list(itertools.combinations(id_collection,2))


        distance_matrix=[]
        #calculate the path between any two points given the id_combinations list and the geojson
        for row in id_combinations:
            z = []
            z.append((row[0],row[1]))
            z.append(vincenty_inverse(self.geojson_obj['features'][row[0]-1]['geometry']['coordinates'],self.geojson_obj['features'][row[1]-1]['geometry']['coordinates']).m)
            distance_matrix.append(z)


        #generate all permutations of a list given the length of the list
        smallest_distance = 1000000000
        smallest_path =[]

        total = math.factorial(len(id_collection))
        c = 0
        perm = itertools.permutations(id_collection,len(id_collection))

        if finishing_point is None:
            for permut in perm:
                c += 1
                if c % (total/100) == 0:
                    print(c/total, " done")
                dist = 0
                if permut[0] == start_point:
                    for step in range(0,len(id_collection)-1):
                        dist += _lookup(permut[step],permut[step+1],distance_matrix) # type: ignore

                    if smallest_distance > dist:
                        smallest_path = permut
                        smallest_distance = dist

        elif start_point is None:
            for permut in perm:
                dist = 0
                if permut[len(permut)-1] == finishing_point:
                    for step in range(0,len(id_collection)-1):
                        dist += _lookup(permut[step],permut[step+1],distance_matrix) # type: ignore

                    if smallest_distance > dist:
                        smallest_path = permut
                        smallest_distance = dist

        else:
            for permut in perm:
                dist = 0
                if permut[0] == start_point and permut[len(permut)-1] == finishing_point:
                    for step in range(0,len(id_collection)-1):
                        dist += _lookup(permut[step],permut[step+1],distance_matrix) # type: ignore

                    if smallest_distance > dist:
                        smallest_path = permut
                        smallest_distance = dist


        return smallest_path



    def nearest_members(self,first_group,second_group,startpoint=1):
        group_path = 1000000000
        neighbours = []




        if isinstance(first_group,int) is True:
          
            a = first_group
            for b in second_group:
                dist = vincenty_inverse(self.geojson_obj['features'][a-1]['geometry']['coordinates'],self.geojson_obj['features'][b-1]['geometry']['coordinates']).m

                if group_path > dist:
                    neighbours=[a,b]
                    group_path = dist
            return neighbours
        elif isinstance(second_group,int) is True:
            b= second_group
            for a in first_group:
                dist = vincenty_inverse(self.geojson_obj['features'][a-1]['geometry']['coordinates'],self.geojson_obj['features'][b-1]['geometry']['coordinates']).m

                if group_path > dist and a != startpoint:
                    neighbours=[a,b]
                    group_path = dist
            return neighbours
        else:
            for a in first_group:
                for b in second_group:
                    dist = vincenty_inverse(self.geojson_obj['features'][a-1]['geometry']['coordinates'],self.geojson_obj['features'][b-1]['geometry']['coordinates']).m

                    if group_path > dist and a != startpoint:
                        neighbours=[a,b]
                        group_path = dist
            return neighbours

    def multi_path(self):

        i=0
        ding =[[None,None]]
        for group in range(len(self.id_groups)-1):
            i += 1 
            neighbours = self.nearest_members(self.id_groups[i-1],self.id_groups[i])
            ding.append(neighbours)
        ding.append([None,None])

        i = 0

        resulting_path = []
        for group in self.id_groups:
            if isinstance(group,int) is True:
                resulting_path.append([group,9999])
            else:
                resulting_path.append(self.__single_path(ding[i][1],ding[i+1][0],group))
            i += 1

        
        self.resulting_path = list(itertools.chain.from_iterable(resulting_path))
        self.resulting_path = [x for x in self.resulting_path if x != 9999]



    def generate_path(self):


        coordinates_sortet =[]
        for step in self.resulting_path:
            
            coordinates_sortet.append(self.geojson_obj['features'][step-1]['geometry']['coordinates'])


        my_line = geojson.LineString(coordinates_sortet)
        self.my_feature = geojson.Feature(geometry=my_line)



        # - first member of second should be fixed and be the closest member to the ending point of the last group.
        # - last member of a group should be fixed and the closest member to any point of the following group.
        # - can'T be the same as the first member