"""
Metrics for determining quality of community structure
"""

import numpy as np
from scipy.sparse import identity

def cluster_total_weight(adj_r, c, cluster_num, dict_bool):
    """Determines the 2*total weight of a community.

    Parameters
    ----------
    adj_r : SciPy sparse matrix (csr or csc)
        The N x N rescaled Adjacency matrix constructed from N x N adjacency matrix of the graph and scale 'r'.
    c : Integer array
        Array of community labels for the nodes in the graph as ordered by the adjacency matrix.
    cluster_num : Integer
        Label of the community of interest.
    dict_bool : dictionary
        Tracks the nodes in each community, with cluster labels as dictionary keys, and
        the corresponding boolean arrays (c == label) as values

    Returns
    -------
    float
        Twice the total weight of all nodes in the rescaled topology of cluster 'cluster_num'.

    """
    bool_r = dict_bool[cluster_num]
    zero = np.zeros(adj.shape[0], dtype = int)
    zero[bool_r] = 1

    return (adj_r[bool_r].dot(zero)).sum()

def cluster_total_volume(adj, c, cluster_num, dict_bool):
    """Determines the volume of a community.

    Parameters
    ----------
    adj : SciPy sparse matrix (csr or csc)
        The N x N rescaled Adjacency matrix constructed from N x N adjacency matrix of the graph and scale r.
    c : Integer array
        Array of community labels for the nodes in the graph as ordered by the adjacency matrix.
    cluster_num : Integer
        Label of the community of interest.
    dict_bool : dictionary
        Tracks the nodes in each community, with cluster labels as dictionary keys, and
        the corresponding boolean arrays (c == label) as values.

    Returns
    -------
    float
        Total volume of all nodes in the rescaled topology of cluster 'cluster_num'.

    """
    return adj[dict_bool[cluster_num]].sum()

def modularity_r(adj, c, cluster_labels, r = 0, dict_bool = None):
    """Determines the modularity (of rescaled topology) for a subset of communities in the network.

    Parameters
    ----------
    adj : SciPy sparse matrix (csr or csc)
        The N x N Adjacency matrix of the graph of interest.
    c : Integer array
        Array of community labels for the nodes in the graph as ordered by the adjacency matrix.
    cluster_labels : Integer array
        Array of unique cluster labels for which modularity is calculated.
    r : float
        Resolution of the topology: smaller 'r' favors larger communities, while larger 'r' favors smaller communities.
    dict_bool : dictionary, optional
        Tracks the nodes in each community, with cluster labels as dictionary keys, and
        the corresponding boolean arrays (c == label) as values.

    Returns
    -------
    float
        total modularity (of rescaled topology) for a set of communities given by 'cluster_labels'.

    """

    I = identity(n = (adj).shape[0])

    #Rescaled adjancency matrix
    adj = adj + (I*r)

    if (dict_bool is None):
        #Track the nodes in each community
        dict_bool = {}
        for label in np.unique(cluster_labels):
            dict_bool[label] = (c == label)

    one = np.ones(adj.shape[0], dtype = int)

    #Twice the total weight of all nodes in the rescaled topology
    total_weight = (adj.dot(one)).sum()

    #Function to determine modularity of each community in the network
    modularize = np.vectorize(lambda cluster_num: (cluster_total_weight(adj, c, cluster_num, dict_bool)/total_weight) -
                         ((cluster_total_volume(adj, c, cluster_num, dict_bool)/total_weight)**2))

    #Total modularity (of rescaled topology) for a set of communities given by 'cluster_labels'
    return np.sum(modularize(cluster_labels))

def split_penalty(adj, c, ci, conn_clusters, total_weight, dict_bool):
    """Determines total Split Penalty density for splitting edges between a community and a set of communities.

    Parameters
    ----------
    adj : SciPy sparse matrix (csr or csc)
        The N x N Adjacency matrix of the graph of interest.
    c : Integer array
        Current array of community labels for the nodes in the graph as ordered by the adjacency matrix.
    ci : Integer
        Label of the community of interest.
    conn_clusters : Integer array
        Array of unique labels of communities that may be connected to the community 'ci'.
    total_weight : float
        Twice the total weight of all nodes in the adjacency matrix.
    dict_bool : dictionary
        Tracks the nodes in each community, with cluster labels as dictionary keys, and
        the corresponding boolean arrays (c == label) as values.

    Returns
    -------
    float
        Total Split Penalty density for splitting edges between 'ci' and a set of other communities in 'conn_clusters'.

    """

    bool_ci = dict_bool[ci]
    adj_ci = adj[bool_ci]

    #Make sure the array of unique labels do not contain 'ci'
    search_bool = (conn_clusters != ci)

    #Determine total split penalty density of splitting edges between 'ci' and 'conn_clusters'
    if(np.sum(search_bool) > 0):
        penalty = sum_penalty(adj_ci, c, conn_clusters[search_bool], dict_bool)/(np.count_nonzero(bool_ci) * total_weight)
    else:
        penalty = 0

    #Total Split Penalty density for splitting edges between 'ci' and a set of other communities in 'conn_clusters'
    return penalty

def individual_penalty(adj_ci, c, cj, dict_bool):
    """Determines partial component of split penalty density for splitting edges between two communities.

    Parameters
    ----------
    adj_ci : SciPy sparse matrix (csr or csc)
        The subset of N X N adjacency matrix: adj[c == ci].
    c : Integer array
        Array of community labels for the nodes in the graph as ordered by the adjacency matrix.
    cj : Integer
        Label of a community connected to the community 'ci'.
    dict_bool : dictionary
        Tracks the nodes in each community, with cluster labels as dictionary keys, and
        the corresponding boolean arrays (c == label) as values.

    Returns
    -------
    float
        Partial component of split penalty density for splitting edges between 'ci' and 'cj'.

    """

    bool_cj = dict_bool[cj]
    zero = np.zeros(len(c), dtype = int)
    zero[bool_cj] = 1

    #Determine partial component of split penalty density for splitting edges between 'ci' and 'cj'
    return ((((adj_ci.dot(zero)).sum())**2)/np.count_nonzero(bool_cj))

def sum_penalty(adj_ci, c, conn_clusters, dict_bool):
    """Determines partial component of total Split Penalty density for splitting edges between a community and a set of communities.

    Parameters
    ----------
    adj_ci : SciPy sparse matrix (csr or csc)
        The subset of N X N adjacency matrix: adj[c == ci].
    c : Integer array
        Array of community labels for the nodes in the graph as ordered by the adjacency matrix.
    conn_clusters : Integer array
        Array of unique labels of communities that may be connected to community 'ci'.
    dict_bool : dictionary
        Tracks the nodes in each community, with cluster labels as dictionary keys, and
        the corresponding boolean arrays (c == label) as values.

    Returns
    -------
    float
        Partial component of total Split Penalty density for splitting edges between 'ci' and a set of other communities in 'conn_clusters'.

    """
    #Function to determine partial component of total Split Penalty density for splitting edges between 'ci' and 'cj'
    penalize = np.vectorize(lambda cj: individual_penalty(adj_ci, c, cj, dict_bool))

    #Partial component of total Split Penalty density for splitting edges between 'ci' and a set of other communities in 'conn_clusters'
    return np.sum(penalize(conn_clusters))

def density_based_modularity(adj, c, ci, total_weight, dict_bool):
    """Determines partial component of modularity density of a community.

    Parameters
    ----------
    adj : SciPy sparse matrix (csr or csc)
        The subset of N X N adjacency matrix: adj[c == ci].
    c : Integer array
        Array of community labels for the nodes in the graph as ordered by the adjacency matrix.
    ci : Integer
        Label of community of interest.
    total_weight : float
        Twice the total weight of all nodes in the adjacency matrix.
    dict_bool : dictionary
        Tracks the nodes in each community, with cluster labels as dictionary keys, and
        the corresponding boolean arrays (c == label) as values.

    Returns
    -------
    float
        Partial component of modularity density of a community 'ci'.

    """

    #Determine Internal community density of 'ci'
    comm_density = community_density(adj, c, ci, dict_bool)

    first_term = (cluster_total_weight(adj, c, ci, dict_bool) * comm_density)/total_weight

    second_term = ((cluster_total_volume(adj, c, ci, dict_bool) * comm_density)/total_weight)**2

    #Partial component of modularity density of 'ci'
    return (first_term - second_term)

def community_density(adj, c, ci, dict_bool):
    """Determines internal community density of a community.

    Parameters
    ----------
    adj : SciPy sparse matrix (csr or csc)
        The subset of N X N adjacency matrix: adj[c == ci].
    c : Integer array
        Array of community labels for the nodes in the graph as ordered by the adjacency matrix.
    ci : Integer
        Label of community of interest.
    dict_bool : dictionary
        Tracks the nodes in each community, with cluster labels as dictionary keys, and
        the corresponding boolean arrays (c == label) as values.

    Returns
    -------
    float
        Determines internal community density of community 'ci'.

    """

    bool_ci = dict_bool[ci]

    zero = np.zeros(adj.shape[0], dtype = int)
    zero[bool_ci] = 1

    #Twice the weight of all edges in the cluster 'ci'
    community_sum = (adj[bool_ci].dot(zero)).sum()

    #Number of nodes in commmunity 'ci'
    size = np.count_nonzero(bool_ci)

    #Internal community density of 'ci'
    density = (community_sum)/(size*(size - 1))

    if(np.isnan(density)):
        density = 0

    #Internal community density of 'ci'
    return density

def compute_modularity_density(adj, c, conn_clusters, cluster_labels, total_weight, dict_bool):
    """Determines modularity density of a set of communities.

    Parameters
    ----------
    adj : SciPy sparse matrix (csr or csc)
        The N x N Adjacency matrix of the graph of interest.
    c : Integer array
        Array of community labels for the nodes in the graph as ordered by the adjacency matrix.
    conn_clusters : Integer array
        Array of unique labels of communities that may be connected to communities in 'cluster_labels'.
    cluster_labels : Integer array
        Array of unique labels of communities of interest.
    total_weight : float
        Twice the total weight of all nodes in the adjacency matrix.
    dict_bool : dictionary
        Tracks the nodes in each community, with cluster labels as dictionary keys, and
        the corresponding boolean arrays (c == label) as values.

    Returns
    -------
    float
        Determines modularity density of a set of communities in 'cluster_labels' with a set of connected communities in 'conn_clusters'.

    """

    #Function to determine modularity density of 'ci' with connected communities in 'conn_clusters'
    mod_density = np.vectorize(lambda ci: density_based_modularity(adj, c, ci, total_weight, dict_bool) - split_penalty(adj, c, ci, conn_clusters, total_weight, dict_bool))

    #Modularity density of a set of communities in 'cluster_labels' with a set of connected communities in 'conn_clusters'
    return np.sum(mod_density(cluster_labels))

def modularity_density(adj, c, cluster_labels, dict_bool = None, conn_clusters = None):
    """Determines modularity_density of a set of communities.

    Parameters
    ----------
    adj : SciPy sparse matrix (csr or csc)
        The N x N Adjacency matrix of the graph of interest.
    c : Integer array
        Current array of community labels for the nodes in the graph as ordered by the adjacency matrix.
    cluster_labels : Integer array
        Array of unique labels of communities of interest.
    dict_bool : dictionary, optional
        Tracks the nodes in each community, with cluster labels as dictionary keys, and
        the corresponding boolean arrays (c == label) as values.
    conn_clusters : Integer array, optional
        Array of unique labels of communities that may be connected to communities in 'cluster_labels'.

    Returns
    -------
    float
        Determines modularity_density of a set of communities in 'cluster_labels'.

    """

    one = np.ones(adj.shape[0], dtype = int)

    #Twice the total weight of all nodes in the adjacency matrix
    total_weight = (adj.dot(one)).sum()

    #Array of unique labels of communities in the network
    unique_clusters = np.unique(c)

    if (dict_bool is None):
        #Track the nodes in each community
        dict_bool = {}
        for label in unique_clusters:
            dict_bool[label] = (c == label)

    if (conn_clusters is None):
        #Array of labels of communities that may be connected to communities in 'cluster_labels'
        conn_clusters = unique_clusters

    #Compute modularity density of a set of communities in 'cluster_labels'
    return compute_modularity_density(adj, c, conn_clusters, cluster_labels, total_weight, dict_bool)
