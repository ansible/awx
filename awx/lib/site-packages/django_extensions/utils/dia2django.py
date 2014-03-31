# -*- coding: UTF-8 -*-
##Author Igor Támara igor@tamarapatino.org
##Use this little program as you wish, if you
#include it in your work, let others know you
#are using it preserving this note, you have
#the right to make derivative works, Use it
#at your own risk.
#Tested to work on(etch testing 13-08-2007):
#  Python 2.4.4 (#2, Jul 17 2007, 11:56:54)
#  [GCC 4.1.3 20070629 (prerelease) (Debian 4.1.2-13)] on linux2

dependclasses = ["User", "Group", "Permission", "Message"]

import re
import six
import sys
import gzip
import codecs
from xml.dom.minidom import *  # NOQA

#Type dictionary translation types SQL -> Django
tsd = {
    "text": "TextField",
    "date": "DateField",
    "varchar": "CharField",
    "int": "IntegerField",
    "float": "FloatField",
    "serial": "AutoField",
    "boolean": "BooleanField",
    "numeric": "FloatField",
    "timestamp": "DateTimeField",
    "bigint": "IntegerField",
    "datetime": "DateTimeField",
    "date": "DateField",
    "time": "TimeField",
    "bool": "BooleanField",
    "int": "IntegerField",
}

#convert varchar -> CharField
v2c = re.compile('varchar\((\d+)\)')


def index(fks, id):
    """Looks for the id on fks, fks is an array of arrays, each array has on [1]
    the id of the class in a dia diagram.  When not present returns None, else
    it returns the position of the class with id on fks"""
    for i, j in fks.items():
        if fks[i][1] == id:
            return i
    return None


def addparentstofks(rels, fks):
    """Gets a list of relations, between parents and sons and a dict of
    clases named in dia, and modifies the fks to add the parent as fk to get
    order on the output of classes and replaces the base class of the son, to
    put the class parent name.
    """
    for j in rels:
        son = index(fks, j[1])
        parent = index(fks, j[0])
        fks[son][2] = fks[son][2].replace("models.Model", parent)
        if parent not in fks[son][0]:
            fks[son][0].append(parent)


def dia2django(archivo):
    models_txt = ''
    f = codecs.open(archivo, "rb")
    #dia files are gzipped
    data = gzip.GzipFile(fileobj=f).read()
    ppal = parseString(data)
    #diagram -> layer -> object -> UML - Class -> name, (attribs : composite -> name,type)
    datos = ppal.getElementsByTagName("dia:diagram")[0].getElementsByTagName("dia:layer")[0].getElementsByTagName("dia:object")
    clases = {}
    herit = []
    imports = six.u("")
    for i in datos:
        #Look for the classes
        if i.getAttribute("type") == "UML - Class":
            myid = i.getAttribute("id")
            for j in i.childNodes:
                if j.nodeType == Node.ELEMENT_NODE and j.hasAttributes():
                    if j.getAttribute("name") == "name":
                        actclas = j.getElementsByTagName("dia:string")[0].childNodes[0].data[1:-1]
                        myname = "\nclass %s(models.Model) :\n" % actclas
                        clases[actclas] = [[], myid, myname, 0]
                    if j.getAttribute("name") == "attributes":
                        for l in j.getElementsByTagName("dia:composite"):
                            if l.getAttribute("type") == "umlattribute":
                                #Look for the attribute name and type
                                for k in l.getElementsByTagName("dia:attribute"):
                                    if k.getAttribute("name") == "name":
                                        nc = k.getElementsByTagName("dia:string")[0].childNodes[0].data[1:-1]
                                    elif k.getAttribute("name") == "type":
                                        tc = k.getElementsByTagName("dia:string")[0].childNodes[0].data[1:-1]
                                    elif k.getAttribute("name") == "value":
                                        val = k.getElementsByTagName("dia:string")[0].childNodes[0].data[1:-1]
                                        if val == '##':
                                            val = ''
                                    elif k.getAttribute("name") == "visibility" and k.getElementsByTagName("dia:enum")[0].getAttribute("val") == "2":
                                        if tc.replace(" ", "").lower().startswith("manytomanyfield("):
                                                #If we find a class not in our model that is marked as being to another model
                                                newc = tc.replace(" ", "")[16:-1]
                                                if dependclasses.count(newc) == 0:
                                                        dependclasses.append(newc)
                                        if tc.replace(" ", "").lower().startswith("foreignkey("):
                                                #If we find a class not in our model that is marked as being to another model
                                                newc = tc.replace(" ", "")[11:-1]
                                                if dependclasses.count(newc) == 0:
                                                        dependclasses.append(newc)

                                #Mapping SQL types to Django
                                varch = v2c.search(tc)
                                if tc.replace(" ", "").startswith("ManyToManyField("):
                                    myfor = tc.replace(" ", "")[16:-1]
                                    if actclas == myfor:
                                        #In case of a recursive type, we use 'self'
                                        tc = tc.replace(myfor, "'self'")
                                    elif clases[actclas][0].count(myfor) == 0:
                                        #Adding related class
                                        if myfor not in dependclasses:
                                            #In case we are using Auth classes or external via protected dia visibility
                                            clases[actclas][0].append(myfor)
                                    tc = "models." + tc
                                    if len(val) > 0:
                                        tc = tc.replace(")", "," + val + ")")
                                elif tc.find("Field") != -1:
                                    if tc.count("()") > 0 and len(val) > 0:
                                        tc = "models.%s" % tc.replace(")", "," + val + ")")
                                    else:
                                        tc = "models.%s(%s)" % (tc, val)
                                elif tc.replace(" ", "").startswith("ForeignKey("):
                                    myfor = tc.replace(" ", "")[11:-1]
                                    if actclas == myfor:
                                        #In case of a recursive type, we use 'self'
                                        tc = tc.replace(myfor, "'self'")
                                    elif clases[actclas][0].count(myfor) == 0:
                                        #Adding foreign classes
                                        if myfor not in dependclasses:
                                            #In case we are using Auth classes
                                            clases[actclas][0].append(myfor)
                                    tc = "models." + tc
                                    if len(val) > 0:
                                        tc = tc.replace(")", "," + val + ")")
                                elif varch is None:
                                    tc = "models." + tsd[tc.strip().lower()] + "(" + val + ")"
                                else:
                                    tc = "models.CharField(max_length=" + varch.group(1) + ")"
                                    if len(val) > 0:
                                        tc = tc.replace(")", ", " + val + " )")
                                if not (nc == "id" and tc == "AutoField()"):
                                    clases[actclas][2] = clases[actclas][2] + ("    %s = %s\n" % (nc, tc))
        elif i.getAttribute("type") == "UML - Generalization":
            mycons = ['A', 'A']
            a = i.getElementsByTagName("dia:connection")
            for j in a:
                if len(j.getAttribute("to")):
                    mycons[int(j.getAttribute("handle"))] = j.getAttribute("to")
            print(mycons)
            if not 'A' in mycons:
                herit.append(mycons)
        elif i.getAttribute("type") == "UML - SmallPackage":
            a = i.getElementsByTagName("dia:string")
            for j in a:
                if len(j.childNodes[0].data[1:-1]):
                    imports += six.u("from %s.models import *" % j.childNodes[0].data[1:-1])

    addparentstofks(herit, clases)
    #Ordering the appearance of classes
    #First we make a list of the classes each classs is related to.
    ordered = []
    for j, k in six.iteritems(clases):
        k[2] = k[2] + "\n    def __unicode__(self):\n        return u\"\"\n"
        for fk in k[0]:
            if fk not in dependclasses:
                clases[fk][3] += 1
        ordered.append([j] + k)

    i = 0
    while i < len(ordered):
        mark = i
        j = i + 1
        while j < len(ordered):
            if ordered[i][0] in ordered[j][1]:
                mark = j
            j += 1
        if mark == i:
            i += 1
        else:
            # swap %s in %s" % ( ordered[i] , ordered[mark]) to make ordered[i] to be at the end
            if ordered[i][0] in ordered[mark][1] and ordered[mark][0] in ordered[i][1]:
                #Resolving simplistic circular ForeignKeys
                print("Not able to resolve circular ForeignKeys between %s and %s" % (ordered[i][1], ordered[mark][0]))
                break
            a = ordered[i]
            ordered[i] = ordered[mark]
            ordered[mark] = a
        if i == len(ordered) - 1:
            break
    ordered.reverse()
    if imports:
        models_txt = str(imports)
    for i in ordered:
        models_txt += '%s\n' % str(i[3])

    return models_txt

if __name__ == '__main__':
    if len(sys.argv) == 2:
        dia2django(sys.argv[1])
    else:
        print(" Use:\n \n   " + sys.argv[0] + " diagram.dia\n\n")
