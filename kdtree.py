
from operator import itemgetter

def dist_min_squared(a, box):
#    d = 0
#    for i, (min_i, max_i) in zip(a,box):
#        if i < min_i:
#             d += (min_i-i)*(min_i-i)
#        elif i > max_i:
#             d += (i-max_i)*(i-max_i)
#    return d
    x = min(max(a[0], box[0][0]), box[0][1])-a[0]
    y = min(max(a[1], box[1][0]), box[1][1])-a[1]
    return x*x + y*y

def dist_squared(a, b, dim):
#    return sum( (j-i)*(j-i) for i, j in zip(a[:dim], b) )
    x, y = b[0]-a[0], b[1]-a[1]
    return x*x + y*y

#def first_index(elements, start, end, key, v):
#    if start == end:
#        return None
#
#    mid = (start + end)//2
#    if elements[mid][key] < v:
#        return first_index(elements, mid+1, end, key, v)
#    elif elements[mid][key] == v:
#        ix = first_index(elements, start, mid, key, v)
#        if ix != None:
#            return ix
#        else:
#            return mid

def subdivide(elements, key, dim):
    if len(elements) == 0:
        return None
    elements.sort(key=itemgetter(key))
#    median = first_index( elements, 0, len(elements)//2+1, key, elements[len(elements)//2][key] ) 
    median = len(elements)//2 
    return ( subdivide(elements[:median],   (key+1)%dim, dim),
             subdivide(elements[median+1:], (key+1)%dim, dim),
             elements[median],
           )

c=0
def nearest(tree, e, box, key, dim, best, limit):
    global c
    c+=1

    l, r, node = tree
    d = dist_squared(node, e, dim)
    if d < limit:# and callback(node, e):
        limit = d
        best = node

    if e[key] < node[key]:
        side_first, side_last = 0, 1
        first, last = l, r
    else:
        side_first, side_last = 1, 0
        first, last = r, l

    if first != None:
        old = box[key][side_first]
        box[key][side_first] = node[key]
        best, limit = nearest(first, e, box, (key+1)%dim, dim, best, limit)
        box[key][side_first] = old

    if last != None:
        old = box[key][side_last]
        box[key][side_last] = node[key]
        if dist_min_squared(e, box) < limit:
            best, limit = nearest(last, e, box, (key+1)%dim, dim, best, limit)
        box[key][side_last] = old

    return best, limit

class KDTree:

    def __init__(self, elements):
        self.dim = 2 #dim
        self.tree = subdivide(elements, 0, self.dim)
        self.box = tuple( [elements[0][i],elements[0][i]] for i in range(self.dim) )
        for e in elements:
            for i,v in enumerate(e[:self.dim]):
                v_min, v_max = self.box[i]
                self.box[i][:] = [min(v_min, v), max(v_max, v)]

    def find_nearest(self, e, limit=None):
        box = tuple( list(l) for l in self.box )
        if limit == None:
            limit = sum( max( (i-i_min)**2, (i-i_max)**2 ) for i, (i_min, i_max) in zip(e, box) ) + 1
        return nearest(self.tree, e, box, 0, self.dim, None, limit)

