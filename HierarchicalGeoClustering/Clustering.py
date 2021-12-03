# AUTOGENERATED! DO NOT EDIT! File to edit: src/01_Clustering.ipynb (unless otherwise specified).

__all__ = ['module_path', 'clustering', 'recursive_clustering', 'compute_dbscan', 'auto_knee_average',
           'compute_hdbscan', 'compute_OPTICS', 'compute_Natural_cities']

# Cell
import os
import sys
module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)
from .TreeClusters import *

# Cell
def clustering(
            t_next_level_2,
            level=None,
            algorithm='dbscan',
            **kwargs
    ):
    """Function to get the clusters for single group by

    :param t_next_level_2 Dictionary with the points to compute the
            cluster
    :param level:  None Level to compute (Default None)

    :param str algorithm : Algorithm type is supported (Default= 'dbscan')

    :param int min_points_cluster:  minimun number of point to consider a cluster(Default 50)

    :param double eps: Epsilon parameter In case is needed

    :param bool return_noise: To return the noise (Default False)

    :param bool verbose: Printing (Dafault False)

    :returns list t_next_level_n: A list with dictionaries with the points, the parent, and nois
    """
    verbose= kwargs.get('verbose',False)
    min_points = kwargs.get( 'min_points_cluster', 50)
    ret_noise= kwargs.get('return_noise', False)
    eps = kwargs.get('eps',0.8)  # Epsilon value to dbscan
    t_next_level_n = []
    if level == None:
        level = 0

    for li_num, cluster_list_D in enumerate(t_next_level_2):
        cluster_list = cluster_list_D['points']
        cluster_list_pa = cluster_list_D['parent']
        if verbose:
            print("Size cluster list: ", len(cluster_list))

        for c_num, cluster in enumerate(cluster_list):
            if verbose:
                print("Size cluster: ", len(cluster))
                print('Algorithm: ', algorithm)

            if len(cluster) > 5:
                if algorithm == 'dbscan':
                    if verbose:
                        print("Epsilon Value: ", eps)
                    tmp = compute_dbscan(cluster,
                                 eps_DBSCAN = eps,
                                 debugg=verbose,
                                  **kwargs)
                    if ret_noise:
                        noise_points = tmp[1]
                        tmp =  tmp[0]


                elif algorithm == 'hdbscan':
                    tmp = compute_hdbscan(cluster,
                                **kwargs)
                    if ret_noise:
                        noise_points = tmp[1]
                        tmp =  tmp[0]
                ##########
                elif algorithm == 'auto_knee_average':
                    #### If the number of cluster is too small

                    tmp = auto_knee_average(cluster, **kwargs)
                    if ret_noise:
                        noise_points = tmp[1]
                        tmp =  tmp[0]

                elif algorithm == 'optics':
                    tmp = compute_OPTICS(cluster,
                                eps_OPTICS = eps,
                                **kwargs)
                    if ret_noise:
                        noise_points = tmp[1]
                        tmp =  tmp[0]
                ##########
                elif algorithm == 'natural_cities':
                    tmp = compute_Natural_cities(cluster,
                                **kwargs)
                    if ret_noise:
                        noise_points = tmp[1]
                        tmp =  tmp[0]
                ##########
                else:
                    raise ValueError('Algorithm must be dbscan or hdbscan')
                    # sys.exit("1")



                if verbose:
                    print("The number of resulting clusters is : ", len(tmp))
                if ret_noise:
                    dic_clos = {'points': tmp,
                           'parent': cluster_list_pa + '_L_'+str(level) +
                            '_l_' + str(li_num) + '_c_'+str(c_num),
                            'noise_points':noise_points
                    }
                else:
                    dic_clos = {'points': tmp, 'parent': cluster_list_pa +
                            '_L_'+str(level) + '_l_' + str(li_num) + '_c_'+str(c_num)}

                t_next_level_n.append(dic_clos)
            else:
                if ret_noise:
                    dic_clos = {'points': [],
                           'parent': cluster_list_pa + '_L_'+str(level) +
                            '_l_' + str(li_num) + '_c_'+str(c_num),
                            'noise_points':cluster
                    }
                else:
                    dic_clos = {'points': [], 'parent': cluster_list_pa +
                            '_L_'+str(level) + '_l_' + str(li_num) + '_c_'+str(c_num)}
                t_next_level_n.append(dic_clos)

    return t_next_level_n

# Cell
def recursive_clustering(
                this_level,  # Dictionary with Points
                to_process,  # levels to process
                cluster_tree,  # to store the clusters
                level = 0,  # current level
                algorithm ='dbscan',  # Algorithm to use
                **kwargs
               ):
    """
    Performs the recursive clustering.
    Calls compute_dbscan for each
    list of clusters keepen the structure and then calls itself
    until no more clusters satisfy the condition

    :param dict this_level: level is the current level

    :param int to_process: the max level to process

    :param double eps: The epsilon parameter distance to pass to the needed algorithm

    :param list cluster_tree : list of list to insert the levels

    :param bool verbose : To print

    :param double decay: In the use of dbscan the deacy parameter to reduce eps

    :param int min_points_cluster: The min point for each cluster to pass to algorithm

    :param str algorithm:  The string of the algorithm name to use
    """

    verbose= kwargs.get('verbose',False)
    min_points = kwargs.get( 'min_points_cluster', 50)
    decay = kwargs.get('decay', 0.7)
    eps = kwargs.get('eps' ,0.8)  # Epsilon distance to DBSCAN parameter
    tmp = None

    if level == 0:
        kwargs['eps'] = eps
    else:
        kwargs['eps'] = eps  * decay

    cluster_result_polygons = []
    if level > to_process:
        if verbose:
            print('Done clustering')
        return
    ######## Get the clusters for the current list of points
    all_l = clustering(
                    this_level,
                    level=level,
                    algorithm=algorithm,

                    **kwargs
                    )
    ##########

    cluster_tree.append(all_l)
    cluster_n = 0
    for i in all_l:
        cluster_n += len(i['points'])
    if verbose:
        print('At level ', level, ' the number of lists are ',
              len(all_l), ' with ', cluster_n, 'clusters')
    level += 1
    if len(all_l) > 0:
        return recursive_clustering(all_l,
                               to_process=to_process,
                               cluster_tree=cluster_tree,
                               level= level,
                               algorithm=algorithm,
                               **kwargs
                               )
    else:
        if verbose:
            print('done clustering')
        return

# Cell
def compute_dbscan(cluster,  **kwargs):

    """
    Sklearn DBSCAN wrapper.

    :param cluster: a (N,2) numpy array containing the obsevations

    :returns list with numpy arrays for all the clusters obtained
    """
    eps = kwargs.get( 'eps_DBSCAN',.04)
    debugg= kwargs.get( 'debugg',False)
    min_samples= kwargs.get( 'min_samples',50)
    ret_noise = kwargs.get('return_noise', False)
    # Standarize sample
    scaler = StandardScaler()
    cluster = scaler.fit_transform(cluster)
    if debugg:
        print('epsilon distance to DBSCAN: ', eps)
        print("min_samples to DBScan: ", min_samples )
        print("Number of points to fit the DBScan: ",cluster.shape[0])

    db = DBSCAN(eps=eps, min_samples=min_samples).fit(cluster)  # Check if can be run with n_jobs = -1

    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_
    l_unique_labels = len(set(labels)) - (1 if -1 in labels else 0)
    unique_labels = set(labels)
    cluster = scaler.inverse_transform(cluster)
    clusters = []
    if debugg:
        print('Number of clusters:' ,l_unique_labels)

    for l in unique_labels:
        if l != -1:
            class_member_mask = (labels == l)
            clusters.append(cluster[class_member_mask])
        elif l == -1 and debugg == True:
            class_member_mask = (labels == l)
            print("Muestras consideradas ruido: ",  sum(class_member_mask))

    if ret_noise == True:
        class_member_mask = (labels == -1)
        return clusters, cluster[class_member_mask]

    return clusters

# Cell
def auto_knee_average(points2_clusters ,
                **kwargs):
    """
    The function use the knee and average to obtain a good value for epsilon and use
    DBSCAN to obtain the clusters

    :param list Points points2_clusters: Point to clusterize

    :param int max_k: = (Default = len(points2_clusters)*.1)

    :param int  min_k: (Default =50)

    :param int step_k: (Default = 50)

    :param int leaf_size: (Default = 50)

    :param bool scale_points: (Default = True)

    :param bool debugg: (Default = False)

    :param bool ret_noise:  (Default = True)

    :returns list : list of cluster. If ret_noise = True return tuple list of cluter and noise
    """
    max_k = kwargs.get('max_k', int(len(points2_clusters)*.1))
    min_k = kwargs.get('min_k', 50)
    step_k = kwargs.get('step_k', 50)
    leaf_size =  kwargs.get('leaf_size',50)
    scale_points= kwargs.get('scale_points',True)
    debugg = kwargs.get('verbose',False)
    ret_noise = kwargs.get('return_noise', True)
    ###### Se tienen que hacer algunos cambios para cuando
    #  los clusters son menores a los minimos establecidos previemente

    ##### Establecer los minimos posibles
    if max_k > len(points2_clusters):
        raise ValueError('The max_k value is too large for the number of points')

    if min_k >  len(points2_clusters):
        print('The min_k value is too large for the number of points returns empty clusters')
        if ret_noise == True:
            return [] , points2_clusters
        else:
            return []

    if step_k > len(points2_clusters):
        raise ValueError('The step_k value is too large for the number of points')


    if min_k == max_k:
        print('min_k reset to obtain at least 1 value')
        min_k = max_k-1

    if scale_points ==True:
        scaler = StandardScaler()
        points_arr = scaler.fit_transform(points2_clusters)
    else:
        points_arr = points2_clusters

    kdt=  cKDTree(points_arr, leafsize=leaf_size)
    lits_appe_all_aver=[]
    for j in range( min_k, max_k, step_k ):
        dist_va, ind = kdt.query(points_arr, k=j, n_jobs =-1)
        non_zero =  dist_va[:, 1:]
        non_zero = np.ndarray.flatten(non_zero)
        non_zero = np.sort(non_zero)
        lis_aver_k=[]
        for i in range(int(non_zero.shape[0]/(j-1)) -1):
            lis_aver_k.append(np.average(non_zero[i*(j-1):(i+1)*(j-1)]))

        average_arr= np.array(lis_aver_k)
        kneedle_1_average = kneed.KneeLocator(
                range(average_arr.shape[0]),
                average_arr,
                curve="convex",## This should be the case since the values are sorted
                direction="increasing", ## This should be the case since the values are sorted incresing
                online=True, ### To find the correct knee the false returns the first find
        )
        epsilon= kneedle_1_average.knee_y
        min_point = kneedle_1_average.knee
        #### We take the average never the less

        lits_appe_all_aver.append({ 'k':j,
                    'Epsilon':epsilon,
                    'value':min_point})

    #### Check if the list is empty
    if len(lits_appe_all_aver) ==0:
        if debugg:
            print('AUTOIMATIC DBSCAN')
            print('Using 0.6 as epsilon and 20 as Minpoints')
        db_scan= DBSCAN(eps=0.6, min_samples=20).fit(points_arr)
    else:
        df_all_average= pd.DataFrame(lits_appe_all_aver)
        max_epsi_all_average= df_all_average['Epsilon'].max()
        if debugg:
            print('Valor de epsion  : ', max_epsi_all_average)
        db_scan= DBSCAN(eps=max_epsi_all_average, min_samples=min_k).fit(points_arr)

    ####Get the clusters
    core_samples_mask = np.zeros_like(db_scan.labels_, dtype=bool)
    core_samples_mask[db_scan.core_sample_indices_] = True
    labels = db_scan.labels_
    unique_labels = set(labels)
    if scale_points ==True:
        points_ret = scaler.inverse_transform(points_arr)
    else:
        points_ret = points_arr
    clusters = []
    for l in unique_labels:
        if l != -1:
            class_member_mask = (labels == l)
            clusters.append(points_ret[class_member_mask])
        elif l == -1 and debugg == True:
            class_member_mask = (labels == l)
            print("Muestras consideradas ruido: ",  sum(class_member_mask))

    if ret_noise == True:
        class_member_mask = (labels == -1)
        return clusters, points_ret[class_member_mask]

    return clusters

# Cell
def compute_hdbscan(points2_clusters,  **kwargs):

    """
    HDBSCAN wrapper.

    :param np.array cluster: a (N,2) numpy array containing the obsevations

    :returns:  list with numpy arrays for all the clusters obtained
    """

    scale_points= kwargs.get('scale_points',True)
    debugg = kwargs.get('verbose',False)
    ret_noise = kwargs.get('return_noise', True)
    min_cluster = kwargs.get('min_cluster', 20)
    if scale_points ==True:
        scaler = StandardScaler()
        points_arr = scaler.fit_transform(points2_clusters)
    else:
        points_arr = points2_clusters

    db = hdbscan.HDBSCAN( ).fit(points_arr)
    core_samples_mask = np.full_like(db.labels_, True, dtype=bool)
    labels = db.labels_
    l_unique_labels = len(set(labels)) - (1 if -1 in labels else 0)
    unique_labels = set(labels)
    if debugg:
        print('total number of clusters: ', len(unique_labels))
    if scale_points ==True:
        points_ret = scaler.inverse_transform(points_arr)
    else:
        points_ret = points_arr
    clusters = []

    for l in unique_labels:
        if l != -1:
            class_member_mask = (labels == l)
            clusters.append(points_ret[class_member_mask])
        elif l == -1 and debugg == True:
            class_member_mask = (labels == l)
            print("Muestras consideradas ruido: ",  sum(class_member_mask))

    if ret_noise == True:
        class_member_mask = (labels == -1)
        return clusters, points_ret[class_member_mask]

    return clusters

# Cell
def compute_OPTICS(points2_clusters,  **kwargs):

    """ OPTICS wrapper.
    :param np.array cluster: a (N,2) numpy array containing the obsevations
    :returns:  list with numpy arrays for all the clusters obtained
    """

    scale_points= kwargs.get('scale_points',True)
    debugg = kwargs.get('verbose',False)
    ret_noise = kwargs.get('return_noise', True)
    min_samples= kwargs.get( 'min_samples',5)
    eps_optics = kwargs.get('eps_optics', None)
    n_jobs = kwargs.get('num_jobs',None)
    xi= kwargs.get('xi',None)
    algorithm_optics= kwargs.get('algorithm_optics','kd_tree')

    if scale_points ==True:
        scaler = StandardScaler()
        points_arr = scaler.fit_transform(points2_clusters)
    else:
        points_arr = points2_clusters


    db = OPTICS(min_samples = min_samples,eps= eps_optics, n_jobs= n_jobs).fit(points2_clusters)
    core_samples_mask = np.full_like(db.labels_, True, dtype=bool)
    labels = db.labels_
    l_unique_labels = len(set(labels)) - (1 if -1 in labels else 0)
    unique_labels = set(labels)
    if debugg:
        print('total number of clusters: ', len(unique_labels))
    if scale_points ==True:
        points_ret = scaler.inverse_transform(points_arr)
    else:
        points_ret = points_arr
    clusters = []

    for l in unique_labels:
        if l != -1:
            class_member_mask = (labels == l)
            clusters.append(points_ret[class_member_mask])
        elif l == -1 and debugg == True:
            class_member_mask = (labels == l)
            print("Muestras consideradas ruido: ",  sum(class_member_mask))

    if ret_noise == True:
        class_member_mask = (labels == -1)
        return clusters, points_ret[class_member_mask]

    return clusters

# Cell
def compute_Natural_cities(points2_clusters,  **kwargs):

    """ Natural_cities.
    :param np.array points2_clusters: a (N,2) numpy array containing the obsevations
    :returns: list with numpy arrays for all the clusters obtained
    """
    ### The function is in acordance with the all the previus functions
    scale_points= kwargs.get('scale_points',True)
    debugg = kwargs.get('verbose',False)
    ret_noise = kwargs.get('return_noise', True)

    if scale_points ==True:
        scaler = StandardScaler()
        points_arr = scaler.fit_transform(points2_clusters)
    else:
        points_arr = points2_clusters

    edges= get_segments(points_arr)
    lenght_av  =  np.average(np.array([i.length for i in edges ]))
    edges = [i for i in edges  if i.length < lenght_av]
    polygons_natural_cities=  get_polygons_buf(edges)
    if debugg:
        if type(polygons_natural_cities)==shapely.geometry.MultiPolygon:
            print('Resulting number of polygons: ', len(polygons_natural_cities))

        elif type(polygons_natural_cities)==shapely.geometry.Polygon:
            print('Only 1 polygon: ')
        else:
            print('The result is not a Polygon or Multipolygon')
    labels_points = labels_filtra(points_arr, polygons_natural_cities)
    core_samples_mask = np.full_like(labels_points, True, dtype=bool)
    l_unique_labels = len(set(labels_points)) - (1 if -1 in labels_points else 0)
    unique_labels = set(labels_points)

    if debugg:
        print('total number of clusters: ', len(unique_labels))
    #### recover
    if scale_points ==True:
        points_ret = scaler.inverse_transform(points_arr)
    else:
        points_ret = points_arr


    clusters = []
    for l in unique_labels:
        if l != -1:
            class_member_mask = (labels_points == l)
            clusters.append(points_ret[class_member_mask])
        elif l == -1 and debugg == True:
            class_member_mask = (labels_points == l)
            print("Muestras consideradas ruido: ",  sum(class_member_mask))

    if ret_noise == True:
        class_member_mask = (labels_points == -1)
        return clusters, points_ret[class_member_mask]

    return clusters