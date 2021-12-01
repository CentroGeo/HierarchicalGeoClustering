# AUTOGENERATED! DO NOT EDIT! File to edit: src/00_Node_cluster.ipynb (unless otherwise specified).

__all__ = ['cluster', 'cluster_node', 'inside_polygon', 'poligon_non_convex_from_Points',
           'poligon_non_convex_random_gen']

# Cell
import sklearn
from sklearn import cluster, datasets
import anytree
from shapely.geometry import LineString
from shapely.ops import polygonize, cascaded_union
from shapely.geometry import box
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import polygonize_full, linemerge, unary_union
from matplotlib import cm
from anytree import NodeMixin, RenderTree

# Cell
class cluster(object):
    polygon_cluster = None
    point_cluster_noise = None

    def __init__(self):
        self.polygon_cluster = None
        self.density = None
        self.point_cluster_noise = None


# Cell
class cluster_node(cluster, NodeMixin):
    def __init__(self,
                name,
                density=None,
                parent=None,
                children=None):
        super(cluster, self).__init__()
        self.name = name
        self.parent = parent
        self.polygon_cluster = None
        if children:
             self.children = children


    def populate_cluster(self,
                    from_points_num=20,
                    density=None,
                    num_points=None,
                    min_scale_x= .1,
                    max_scale_x=.5,
                    min_scale_y= .1,
                    max_scale_y=.5,
                    random_state= 170,
                    **kwargs
                    ):
        self.density = density
        random.seed(random_state) ## initialize random state
        avoid_intersec= kwargs.get('avoid_intersec', False)
        if self.parent is None:
            self.polygon_cluster = self.create_polygon(from_points_num)
            new_pol_x_min, new_pol_y_min, new_pol_x_max, new_pol_y_max = self.polygon_cluster.bounds
            self.center = shapely.geometry.Point((new_pol_x_max -new_pol_x_min)/2 + new_pol_x_min,
                             (new_pol_y_max- new_pol_y_min)/2+new_pol_y_min)

        else:
            #### create the polygon inside the parent

            if self.parent.polygon_cluster ==None:
                raise ValueError('The parent has no polygon')

            # print('parent name:',self.parent.name)
            ########
            #### Vamos a pedirle que no este en el polygono de los hijos
            random_point_center = self.parent.get_random_points(1, random_state)[0]

            #### create polygon and scale

            polygon = self.create_polygon(from_points_num)
            new_pol_x_min, new_pol_y_min, new_pol_x_max, new_pol_y_max = polygon.bounds
            center_polygon = shapely.geometry.Point((new_pol_x_max -new_pol_x_min)/2 + new_pol_x_min,
                             (new_pol_y_max- new_pol_y_min)/2+new_pol_y_min)
            translate = shapely.geometry.Point(
                            random_point_center.x -center_polygon.x,
                            random_point_center.y -center_polygon.y
                            )
            polygon = shapely.affinity.translate(
                        polygon,
                        xoff = translate.x,
                        yoff = translate.y
                        )
            new_pol_x_min, new_pol_y_min, new_pol_x_max, new_pol_y_max = polygon.bounds
            esq = [
                shapely.geometry.Point(new_pol_x_min,new_pol_y_min ),
                shapely.geometry.Point(new_pol_x_min,new_pol_y_max ),
                shapely.geometry.Point(new_pol_x_max,new_pol_y_min ),
                shapely.geometry.Point(new_pol_x_max,new_pol_y_max )
              ]
            max_dis_esq = max([random_point_center.distance(i) for i in esq])

            ###### Scale the polygon
            #dis_poly_parent= self.parent.polygon_cluster.exterior.distance(random_point_center)

            max_dis = self.parent.polygon_cluster.exterior.distance( random_point_center)

            fact_pol = (max_dis/(1.3*max_dis_esq))

            scale_factor_max_x  = min (fact_pol, max_scale_x)
            scale_factor_max_y  = min (fact_pol, max_scale_y)


            # print('scale x:', scale_factor_max_x)
            # print('scale y:', scale_factor_max_y)
            ##########
            polygon= shapely.affinity.scale(
                polygon,
                xfact=scale_factor_max_x,
                yfact=scale_factor_max_y,
                origin= random_point_center
            )

            ###### A qui se tiene que verificar si ha caido en alguno.
            if avoid_intersec == False:
                self.polygon_cluster  = polygon
                self.center = random_point_center
            else:
                ### Se tiene que modificar
                self.polygon_cluster, self.center = self.parent.polygon_not_in_children(random_state= random_state)


        ############### The points
        if self.polygon_cluster is None:
            raise ValueError('No polygon in the cluster')

        if self.density is not None:
            npoints_polygon  = int(self.polygon_cluster.area*density)
            #print(npoints_polygon)
            self.point_cluster_noise = self.create_random_points(npoints_polygon)
        elif self.density is None and num_points is not None:
            self.density = num_points /self.polygon_cluster.area
            #print(num_points)
            self.point_cluster_noise = self.create_random_points(num_points)


    ##### Generate random polygon
    def create_polygon(self,  from_points_num=20):
        polygon = poligon_non_convex_random_gen(from_points_num)
        while type(polygon) == shapely.geometry.MultiPolygon:
            polygon = poligon_non_convex_random_gen(
                from_points_num)
        return polygon


    def get_random_points(self, n_points, random_state= 150):
        """
        Returns random points inside the cluster polygon
        :param n_points Number of point to be generated
        :param random_state Random state
        :returns: A list with points
        """
        random.seed(random_state)
        x_min, y_min ,x_max, y_max =self.polygon_cluster.bounds
        ret_points= []
        while len(ret_points)< n_points:
            x_rand = random.uniform(x_min, x_max)
            y_rand = random.uniform(y_min, y_max)
            point_s =shapely.geometry.Point(x_rand, y_rand)

            if self.polygon_cluster.contains(point_s):
                ret_points.append(point_s)


        return ret_points
    #### create random_points
    def create_random_points(self, npoints_polygon=1000, random_state = 120):
        """
        Create random points
        :param npoints_polygon Number of point to get
        :random_state Random state integer to ste random
        :returns: A shapely multyPoint clas witn npoints_polygon points

        """
        random.seed(random_state)
        minx_b, miny_b, maxx_b, maxy_b = self.polygon_cluster.bounds
        point_cluster_noise = []
        while len(point_cluster_noise) < npoints_polygon:
            points_cluster = np.random.random_sample(
                (int(npoints_polygon*1.2), 2))
            points_cluster[:, 0] = (maxx_b - minx_b) * \
                points_cluster[:, 0] + minx_b
            points_cluster[:, 1] = (maxy_b - miny_b) * \
                points_cluster[:, 1] + miny_b
            points_cluster = shapely.geometry.MultiPoint(list(points_cluster))
            points_cluster_o = [p for p in points_cluster if
                                self.polygon_cluster.contains(p)
                                ]
            point_cluster_noise = point_cluster_noise + points_cluster_o

        point_cluster_noise = shapely.geometry.MultiPoint(point_cluster_noise[:npoints_polygon])

        return point_cluster_noise




    def scale(self,x_scale, y_scale, center_scale= 'center'):
        """
        Scale the points in the cluster
        :param x_scale Scale factor to scale in x axis
        :param y_scale Scale factor to scale in y axis
        :param center_scale Scale center point  (Default = 'center')
        :returns: No returns
        """
        if self.point_cluster_noise is not None:
            self.point_cluster_noise = shapely.affinity.scale(
                                    self.point_cluster_noise,
                                    xfact=  x_scale,
                                    yfact=  y_scale,
                                    origin = center_scale
                                    )
        if  self.polygon_cluster is not None:
            self.polygon_cluster = shapely.affinity.scale(
                                    self.polygon_cluster,
                                    xfact=  x_scale,
                                    yfact=  y_scale,
                                    origin = center_scale
                                    )
        ########Se deberian escalar todos #2 sus nodos hijos
        #

    def get_density(self):
        """
        Get the density if the cluster
        Number of point in the cluster/Area of the polygon cluster
        :returns the density of the node
        """
        if self.density is not None:
            return self.density
        else:
            if self.polygon_cluster is None:
                print("Cluster has no polygon")
                self.density = None
                return self.density
            else:
                if self.polygon_cluster is not None:
                    if self.point_cluster_noise is None:
                        print('the node has no points')
                        return 0
                    else:
                        self.density = len(self.point_cluster_noise)/self.polygon_cluster.area
                        return self.density





    ###### Get center

    def get_center(self):
        """
        returns the center of the bounding box poligon
        :returns: Shapely Point center
        """
        if self.center is not None:
            return self.center
        else:
            if self.polygon_cluster is None:
                print("Cluster has no polygon")
                return None
            else:
                bou = new.polygon_cluster.bounds
                x=(bou[2]-bou[0])/2
                y=(bou[3]-bou[1])/2
                self.center = shapely.geometry.Point(x,y)
                return self.center




    ##### Get Points get the noise points of the cluster
    def get_points(self, all_tag = False ):
        """
        Returns the noise point of the cluster, if all_tag is set true returns
        all the points of the its decendents
        """
        if all_tag == False:
            return self.point_cluster_noise
        else :
            all_points = []
            if self.parent is None:
                all_points.append((self.point_cluster_noise, self.name  ))
            else:
                all_points.append((self.point_cluster_noise, self.parent.name + '_' +self.name))

            for child in self.children:
                all_points= all_points + child.get_points(all_tag = all_tag)

        return  all_points

    def get_point_decendent(self):
        """returns all the point of the node and its decendents
        """
        all_p  = []
        all_p= all_p+ [i for i in self.get_points()]
        for child in self.children:
            all_p= all_p +child.get_point_decendent()
        return all_p


    ######Tag the points
    def tag_low_level(self, point_check= None):
        """
        The tag the element of the node using the labels noise or the child name
        as a tag, if a set of point is pass (point_check != None)
        the elements are treated as part of the cluster and label it accordingly.
        :params self
        :params point_check A list MultiPoint or list with Points to tag
        """

        if point_check is None:
            all_points_cluster = self.get_points()
        else:
            #all_points_cluster = self.get_points()
            all_points_cluster = point_check
        # print('Leng to check:', len(all_points_cluster))
        all_point_tag = []
        for point in all_points_cluster:
            point_tag= ''
            for id_child, child in enumerate(self.children):
                if child.polygon_cluster.contains(point):
                    if child.name is None:
                        point_tag = point_tag+str(id_child)
                    else:
                        if point_tag== '':
                            point_tag = child.name
                        else:
                            point_tag = point_tag +'_'+ child.name

            if point_tag=='':
                    point_tag = self.name+'_'+'noise'
            all_point_tag.append((point,point_tag))
        return all_point_tag
#######
##############tag level

    def tag_low_level_noise_signal(self, point_check= None):
        """
        The tag the element of the node using the labels noise or signal
        as a tag, if a set of point is pass (point_check != None)
        the elements are treated as part of the cluster and label it
        accordingly.
        :params self
        :params point_check A list MultiPoint or list with Points to tag
        """
        if point_check is None:
            all_points_cluster = self.get_points()
        else:
            #all_points_cluster = self.get_points()
            all_points_cluster = point_check
        # print('Leng to check:', len(all_points_cluster))
        all_point_tag = []
        for point in all_points_cluster:
            point_tag= ''
            for id_child, child in enumerate(self.children):
                if child.polygon_cluster.contains(point):
                    if child.name is None:
                        point_tag = point_tag+'1'
                    else:
                        if point_tag== '':
                            point_tag = '1'
                        else:
                            point_tag = point_tag +'_'+ '1'

            if point_tag=='':
                point_tag = 'noise'
            all_point_tag.append((point,point_tag))
        return all_point_tag

    #### iterative tag
    def tag_all_point(self, to_tag = None):
        """
        Returns all the points and the points of it decendents tag,
        the tags are the name of the nodes
        """
        level_tags_self = self.tag_low_level()
        if to_tag is not None:
            #### to tag has to be in the same form as the return of tag_low
            to_tag_point  = [i[0] for i in to_tag ]
            to_tag_labels = [i[1] for i in to_tag ]
            to_tag_point= self.tag_low_level(to_tag_point)
            merge_labes_re_labels =zip(to_tag_point, to_tag_labels)
            to_tag_result = [(i[0][0], i[1]+'+'+i[0][1]) for i in merge_labes_re_labels]
            level_tags_self = level_tags_self + to_tag_result

        ### Pass to children
        level_tags_children = [i for i in level_tags_self if self.name + '_noise' not in i[1] ]
        not_children = [i for i in level_tags_self if self.name + '_noise' in i[1] ]
        tag_from_children = []
        for child in self.children:
            # print(child.name)
            level_tags_pass_children =  [i for i in level_tags_children if i[1] == child.name   ]
            tag_from_children = tag_from_children + child.tag_all_point( level_tags_pass_children)


        return not_children +tag_from_children

    ##################iterative tag noise signal

    def tag_all_point_noise_signal(self, to_tag = None):
        """
        Returns all the points and the points of it decendents tag or
        noise

        """
        level_tags_self = self.tag_low_level_noise_signal()
        if to_tag is not None:
            #### to tag has to be in the same form as the return of tag_low
            to_tag_point  = [i[0] for i in to_tag ]
            to_tag_labels = [i[1] for i in to_tag ]
            to_tag_point= self.tag_low_level_noise_signal(to_tag_point)
            merge_labes_re_labels =zip(to_tag_point, to_tag_labels)
            to_tag_result = [(i[0][0], i[1]+'+'+i[0][1]) for i in merge_labes_re_labels]
            level_tags_self = level_tags_self + to_tag_result

        ### Pass to children
        level_tags_children = [i for i in level_tags_self if '1' in i[1] ]
        not_children = [i for i in level_tags_self if  'noise' in i[1] ]
        tag_from_children = []
        for child in self.children:
            # print(child.name)
            level_tags_pass_children =  [i for i in level_tags_children if i[1] == '1'   ]
            tag_from_children = tag_from_children + child.tag_all_point_noise_signal( level_tags_pass_children)


        return not_children +tag_from_children


    ######Check point for children
    def check_point_children(self, Points_tocheck):
        point_chek_bool=[]
        for child in self.children:

            if child.polygon_cluster is not None:
                point_chek_bool.append([child.polygon_cluster.contains(i) for i in Points_tocheck])
            else:
                point_chek_bool.append([])
        return point_chek_bool

    ########## viewer
    def viewer_cluster(self, ax,  **kwargs):
        level_view = kwargs.get('level', 0 )
        polygon_con= kwargs.get('polygon', False)
        poligon_children = kwargs.get('polygon_children', False)
        if level_view == 0:
            cluster_points = self.get_points()
            x_points_cluster =[j.x for j in cluster_points  ]
            y_points_cluster =[j.y for j in cluster_points  ]
            ax.scatter(x_points_cluster,y_points_cluster,
                    s = kwargs.get('size_cluster', 1),
                    color = kwargs.get('color_cluster', 'orange'),
                    alpha = kwargs.get('alpha_cluster', .5)
                    )
        elif  level_view ==1:
            cluster_points = self.get_points()
            x_points_cluster =[j.x for j in cluster_points  ]
            y_points_cluster =[j.y for j in cluster_points  ]
            ax.scatter(x_points_cluster,y_points_cluster,
                    s = kwargs.get('size_cluster', 2),
                    color = kwargs.get('color_cluster', 'green'),
                    alpha = kwargs.get('alpha_cluster', .5)
                    )

            for child in self.children:
                child_points = child.get_points()
                x_points_children = [j.x  for j in child_points   ]
                y_points_children = [j.y  for j in child_points   ]
                ax.scatter(
                    x_points_children,
                    y_points_children,
                    s = kwargs.get('size_children', 1),
                    color = kwargs.get('color_children', 'blue'),
                    alpha = kwargs.get('alpha_children', .25)
                    )
                if poligon_children== True:
                    x_polygon, y_polygon  =child.polygon_cluster.exterior.xy
                    ax.plot(x_polygon, y_polygon,
                    color= kwargs.get(
                        'polygon_color_children',
                        'blue')
                    )
        elif  level_view == -1:
            jet =  plt.get_cmap('jet')
            cNorm  = matplotlib.colors.Normalize(vmin=0, vmax=250)
            scalarMap = matplotlib.cm.ScalarMappable(norm=cNorm, cmap=jet)
            color_random=random.randint(0, 250)
            ax = self.viewer_cluster(ax,
                    level = 0,
                    size_cluster = kwargs.get('size_cluster', 1),
                    color_cluster= scalarMap.to_rgba(color_random),
                    alpha_cluster = kwargs.get('alpha_cluster', .5),
                    polygon = polygon_con

            )
            kwargs['polygon_color']= scalarMap.to_rgba(color_random)
            for child in self.children:
                 child.viewer_cluster(ax, **kwargs)

        if polygon_con:
            x_polygon, y_polygon  =self.polygon_cluster.exterior.xy
            ax.plot(x_polygon,
                    y_polygon,
                    color= kwargs.get(
                            'polygon_color',
                            'magenta'
                        )
                    )

        return ax


    ################## Dynamic generation
    ###



    def reproduce_node_polygon(
                self,
                **kwargs
                ):
        percent_construc_poligon = kwargs.get( 'percent_construc_poligon',.85)
        u= kwargs.get( 'u', 20)
        ###### The factors has to be symilar respect to the bounding box

        x_fac = kwargs.get('x_fac', 0.01)
        y_fac = kwargs.get('y_fac', 0.01)
        b_val= kwargs.get('b_val', 1.2)
        list_child = kwargs.get('list_children', None)
        random_seed= kwargs.get('random_seed', 142)
        verbose= kwargs.get('verbose', False )

        if self.polygon_cluster is None:
            raise ValueError('No polygon in the cluster no able to reproduce')


        ### Duplicate the node using a similar poligon
        min_x_pol, min_y_pol , max_x_pol , max_y_pol = self.polygon_cluster.bounds

        ####Get bounding boxes of the nodes child poligons
        if self.children is not None:
            if list_child is not None:
                bounds_children = [d.polygon_cluster.bounds for d, s in zip(self.children, list_child) if s]
                print(bounds_children)
            else:
                bounds_children =[child.polygon_cluster.bounds for child in  self.children]

            points_bound_children  = [shapely.geometry.Point(bound[0], bound[1]) for bound in bounds_children  ]
            points_bound_children  = points_bound_children  + [shapely.geometry.Point(bound[0], bound[3]) for bound in bounds_children ]
            points_bound_children  = points_bound_children  + [shapely.geometry.Point(bound[2], bound[1]) for bound in bounds_children ]
            points_bound_children  = points_bound_children  + [shapely.geometry.Point(bound[2], bound[3]) for bound in bounds_children ]
            x_side_val = abs(max_x_pol- min_x_pol)
            y_side_val = abs(max_y_pol- min_y_pol)
            x_min_val =  min_x_pol - x_side_val*x_fac
            x_max_val =  max_x_pol + x_side_val*x_fac
            y_min_val =  min_y_pol - y_side_val*y_fac
            y_max_val =  max_y_pol + y_side_val*y_fac
            random_points_pol_new=[]
            res_bool = False
            if verbose==True:
                print('X Minimun value:', x_min_val)
                print('X Maximun value:', x_max_val)
                print('Y Minimun value:', x_min_val)
                print('Y Maximun value:', x_max_val)
            random.seed(random_seed)
            while  res_bool ==False:
                for i in range(u):
                    random_points_pol_new.append(
                                    shapely.geometry.Point(
                                                random.uniform(x_min_val, x_max_val  ),
                                                random.uniform(y_min_val, y_max_val  )
                                    )
                    )
                res_bool , random_points_pol_new = inside_polygon(random_points_pol_new,
                                                                self.polygon_cluster,
                                                                percent_construc_poligon
                                                                )
            random_points_pol_new = random_points_pol_new + points_bound_children

        return poligon_non_convex_from_Points(random_points_pol_new)

    def duplicate_node(self,
                       **kwargs):
        """
        The function "duplicate" the cluster node
        returns : a cluster_node class
        """

        pref=kwargs.get('copy_pref', 'copy_')
        new_cluster = cluster_node( pref+ self.name )
        density_in = kwargs.get('parent', None)
        parent_in= kwargs.get('parent', None),
        children_in = kwargs.get('children', None)
        npoints_in = kwargs.get('npoints', None)


        new_cluster.polygon_cluster = self.reproduce_node_polygon(**kwargs )


        if density_in is None:
            new_cluster.density = self.get_density()
        else:
            new_cluster.density = density

        if npoints_in is None:
            npoints = math.floor(new_cluster.density * new_cluster.polygon_cluster.area )
            new_cluster.point_cluster_noise =  new_cluster.get_random_points(npoints)
        else:
            ### overided the density
            new_cluster.density = npoint_in/new_cluster.cluster_polygon.area
            new_cluster.point_cluster_noise =  new_cluster.get_random_points(npoints)



        return new_cluster
    ##########Get polygon no toching with others
    def polygon_not_in_children(self, **kwargs):

        """
        El nodo que se pasa como parametro debe ser el padre del poligono que se pide
        y el poligon estara contenido dentro del pologon del nodo que esta como parametro

        """
        random_state=kwargs.get('random_state', 123456)
        from_points_num= kwargs.get('from_points_num', 20)
        max_scale_x = kwargs.get('max_scale_x',.5)
        max_scale_y = kwargs.get('max_scale_y',.5)
        chec_in= True
        while chec_in ==True:
            random_point_center = self.get_random_points(1, random_state)[0]
            chec_in=all(self.check_point_children([random_point_center]))
        ### create polygon and scale

        polygon = self.create_polygon(from_points_num)
        new_pol_x_min, new_pol_y_min, new_pol_x_max, new_pol_y_max = polygon.bounds
        center_polygon = shapely.geometry.Point((new_pol_x_max -new_pol_x_min)/2 + new_pol_x_min,
                    (new_pol_y_max- new_pol_y_min)/2+new_pol_y_min)
        translate = shapely.geometry.Point(
                    random_point_center.x -center_polygon.x,
                    random_point_center.y -center_polygon.y
                    )
        polygon = shapely.affinity.translate(
                polygon,
                xoff = translate.x,
                yoff = translate.y
                )
        new_pol_x_min, new_pol_y_min, new_pol_x_max, new_pol_y_max = polygon.bounds
        esq = [ shapely.geometry.Point(new_pol_x_min,new_pol_y_min ),
                shapely.geometry.Point(new_pol_x_min,new_pol_y_max ),
                shapely.geometry.Point(new_pol_x_max,new_pol_y_min ),
                shapely.geometry.Point(new_pol_x_max,new_pol_y_max )
            ]
        max_dis_esq = max([random_point_center.distance(i) for i in esq])

    ###### Scale the polygon
    #dis_poly_parent= self.parent.polygon_cluster.exterior.distance(random_point_center)
        ###### Para que no toque con los hijos lo que debemos pedir es que esta distancia
        # sea con respecto a la distancia minima de los poligonos de los hijos

        max_dis_parent = self.polygon_cluster.exterior.distance( random_point_center)
        min_dis_children= []
        for child  in self.children:
            if child.polygon_cluster is not None:
                min_dis_children.append(child.polygon_cluster.exterior.distance(random_point_center))
            else:
                min_dis_children.append(300000000000000) #### Es un numero cualquiera
        max_dis_children_all= min(min_dis_children)##### Es tomar la minima distancia
        max_dis = min (max_dis_children_all, max_dis_parent)

        fact_pol = (max_dis/(1.3*max_dis_esq))

        scale_factor_max_x  = min (fact_pol, max_scale_x)
        scale_factor_max_y  = min (fact_pol, max_scale_y)


    # print('scale x:', scale_factor_max_x)
    # print('scale y:', scale_factor_max_y)
    ##########
        polygon= shapely.affinity.scale(
            polygon,
            xfact=scale_factor_max_x,
            yfact=scale_factor_max_y,
            origin= random_point_center
        )
        return polygon, random_point_center


# Cell
def inside_polygon(list_points, poligon_check, min_percent):
    """
    Help function to validate the number of points that are inside the polygon
    :param list list_points: List of points to concider
    :param shapely.geometry.Polygon poligon_check:
    :param min_percent: Minimun percent of point to be consider inside
    :returns bool: True If the amount of points are inside.
    """
    if len(list_points)< 2:
        return False
    inside = [i for i in list_points if poligon_check.contains(i) ]
    #print(len(inside))
    if len(inside) > int(min_percent*len(list_points)):

        return True , list_points
    else:

        return False , inside

# Cell
def poligon_non_convex_from_Points( points_li ):
    """Create a random (no convex) poligon from the points
    The algorithm returns a polygon creatated from the points, the
    non convex part it is not always guaranteed.
    :param list points_li: list of shapely.geometry.Point
    :returns shapely.grometry.Polygon: The polygon created
    """

    triangles = shapely.ops.triangulate(shapely.geometry.Polygon(points_li))
    Pol = shapely.geometry.Polygon(points_li).convex_hull
    remove_triangles = []
    keep_triangles = []
    for i in triangles:
        inter = Pol.exterior.intersection(i)
        if type(inter) == shapely.geometry.linestring.LineString and inter.length != 0.0:
            remove_triangles.append(i)
        else:
            keep_triangles.append(i)
    return shapely.ops.cascaded_union(keep_triangles)

# Cell
def poligon_non_convex_random_gen(npoints):
    """Create a random (no convex) poligon from n points
    The algorithm returns a polygon creatated from n random 2d points the
    non convex part it is not always guaranteed.
    :param int npoints: Number of point to generate the polygon
    :returns shapely.grometry.Polygon: The poligon created
    """
    points_r = np.random.random((npoints, 2))
    triangles = shapely.ops.triangulate(shapely.geometry.Polygon(points_r))
    Pol = shapely.geometry.Polygon(points_r).convex_hull
    remove_triangles = []
    keep_triangles = []
    for i in triangles:
        inter = Pol.exterior.intersection(i)
        if type(inter) == shapely.geometry.linestring.LineString and inter.length != 0.0:
            remove_triangles.append(i)
        else:
            keep_triangles.append(i)
    return shapely.ops.cascaded_union(keep_triangles)