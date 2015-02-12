## Implement the web page for cache agent
## Chen Wang, Feb. 12, 2015
## chenw@cmu.edu
# Package: cache.web_agent

import os


# ================================================================================
# Return a web page that shows all files under the current path
# ================================================================================
def make_index( relpath ):     
    abspath = os.path.abspath(relpath) # ; print abspath
    flist = os.listdir( abspath ) # ; print flist
     
    rellist = []     
    for fname in flist :     
        # relname = os.path.join(relpath, fname)
        # rellist.append(relname)
        rellist.append(fname)
     
     # print rellist
    inslist = []     
    for r in rellist :     
        inslist.append( '<a href="%s">%s</a><br>' % (r,r) )
     
    # print inslist
     
    page_tpl = "<html><head></head><body>%s</body></html>"         
    ret = page_tpl % ( '\n'.join(inslist) , )
     
    return ret

def welcome_page():
    page = "<html>  \
                <title>  \
                    AGENP Cache Agent \
                </title> \
                <body>  \
                    <h1> Welcome!! </h1>\
                    <p>This is the cache agent in AGENS system </p>\
                    <p>You can use '/videos' to show all available videos in local cache! </p>\
                </body> \
            </html>"
    return page