#
# CoExplorer
#
# Model/Metamodel co-explorer for Modelio.
#
# Author: jmfavre
# 
# History
#   Version 0.3 - October 28, 2013
#      - port to Modelio 3 
#   Version 0.2 - October 25, 2013
#      - addition of SWT GUI for the co-explorer
#   Version 0.1 - October 25, 2013
#      - first version for Modelio 2.2
#      - basic functions
#      - showInfo functions


# check if this is modelio 3 because the API has changed
try:
  from org.modelio.api.modelio import Modelio
  orgVersion = True
except:
  from com.modeliosoft.modelio.api.modelio import Modelio
  orgVersion = False
from org.eclipse.core.runtime import IAdaptable
from misc import reject,excluding,exists,isEmpty,notEmpty,isList,forAll,isString
from misc import HtmlWindow,TreeWindow
from misc import getWebPage

__all__ = [
  "getMetaclassFromName",
  "getNameFromMetaclass",
  "isMetaclass",
  "isEnumeration",
  "getNameFromType",
  "getMetaclassImage",
  "getMetaclassJavadocURL",
  "getMetaclassMetamodelURL",
  "getSubMetaclasses",
  "getSuperMetaclasses",
  "MetaFeature",
  "getMetaFeatures",
  
  "MetaclassInfo",
  "getMetaclassInfo",
  
  "isElement",
  "isElementList",
  "isScalar",
  "isEnumerationLiteral",
  "isAtomic",
  "getElementId",
  "getElementNameOrId",
  "getElementSignature",
  
  "getMetaclass",
  "getElementInfo",
  "MetaFeatureSlots",
  "getMetaFeatureSlots",
  
  "ElementInfo",
  "getElementInfo",

  "getAllInstances",
  "getSelectedInstances",
  "getModelRoot",
  "getElementParent",
  "getElementParents",
  "getElementPath",
  
  "show",
  "elementTree",
  
  #---- some examples
  "showUseCasesPerActors"
  
   
 ]

SPECIAL_FEATURES = [ 
  "toString","hashCode","compareTo","wait",
  "accept",
  "notify","notifyAll",
  "class","getClass",
  "delete","getmodifDate","isValid",
  "hid","getHid","lid","getLid","getMetaclassId","sessionId","getSessionId","getElementStatus"]

MODELIO = Modelio.getInstance()
METAMODEL_SERVICE = MODELIO.getMetamodelService()
MODELING_SESSION  = MODELIO.getModelingSession()

if orgVersion:
  from org.modelio.metamodel.uml.infrastructure import Element as ModelioElement
else:
  from com.modeliosoft.modelio.api.model.uml.infrastructure import IElement as ModelioElement

# useful for python introspection
def _isPythonBuiltin(name): 
  return name.startswith('__') and name.endswith('__')

def getMetaclassFromName(metaclassname):
  """ get the Modelio Metaclass inheriting from ModelioElement and 
     corresponding to the given name of a metaclass.
     Return null if the name provided is not the name of a metaclass 
  """
  return METAMODEL_SERVICE.getMetaclass(metaclassname)

def getNameFromMetaclass(metaclass):
  """ get the name of a metaclass  
  """
  # TODO
  if issubclass(metaclass,ModelioElement):
    name = METAMODEL_SERVICE.getMetaclassName(metaclass)
  else:
    name = unicode(metaclass.getCanonicalName())
  return unicode(name)

def isJavaClass(x):
  return isinstance(x,java.lang.Class)
  
def isMetaclass(x,justInterfaces=False):
  """ return true if the argument is a metaclass or a implementation of a metaclass
  """
  return isJavaClass(x) \
         and getNameFromMetaclass(x) is not None \
         and (not justInterfaces or x.isInterface())  

def isEnumeration(x):
  """ return true if x is an enumeration type
  """
  try:
    return issubclass(x,java.lang.Enum)
  except:
    return False  
  
def getNameFromType(t):
  """ get name from a type, i.e. a metaclass or a basic type
  """
  if t is java.lang.String:
    name = "string"
  elif isEnumeration(t):
    # enumeration type are NOT interfaces in modelio api and are named
    # like com.modeliosoft.modelio.api.model.uml.statik.ObVisibilityModeEnum
    # We remove the path, leaving ObVisibilityModeEnum
    name = t.getCanonicalName().split('.')[-1]
  else:
    try: 
      name = getNameFromMetaclass(t)
    except:
      name = None
    if name is None:
      try:
        name = t.__name__
      except:
        try:
          name = t.name
        except:
          try:
            name = t.getName()
          except:
            try:
              name = t.toString()
            except:
              name = "<unamed type>"
  return unicode(name)
  
def getMetaclassImage(metaclass):
  """ return the image corresponding to a metaclass or None if no image is available
  """
  try:
    return Modelio.getInstance().getImageService().getMetaclassImage(metaclass)
  except:
    return None

MODELIO_VERSION = Modelio.getInstance().getContext().getVersion()
MODELIO_DOC_URL_ROOT = "http://modelio.org/documentation"
MODELIO_SIMPLE_VERSION = str(MODELIO_VERSION.getMajorVersion())+'.'+str(MODELIO_VERSION.getMinorVersion())
MODELIO_JAVADOC_ROOT_URL = MODELIO_DOC_URL_ROOT+"/javadoc-"+MODELIO_SIMPLE_VERSION
if MODELIO_VERSION.getMajorVersion() <= 2:
  MODELIO_PACKAGES_PREFIX = "com.modeliosoft."
else:
  MODELIO_PACKAGES_PREFIX = "org.modelio."
  

def getMetaclassJavadocURL(metaclass):
  """ return the url of 
  """
  try:
    name = metaclass.getCanonicalName()
    # print "name=",name,MODELIO_PACKAGES_PREFIX
    if name.startswith(MODELIO_PACKAGES_PREFIX):
      return MODELIO_JAVADOC_ROOT_URL+"/"+name.replace(".","/")+".html"
    else:
      return None
  except:
    return None

MODELIO_METAMODEL_ROOT_URL = MODELIO_DOC_URL_ROOT+"/metamodel-"+MODELIO_SIMPLE_VERSION
METAMODEL_INDEX_URL = MODELIO_METAMODEL_ROOT_URL+"/modelbrowser.html"
METAMODEL_ROOT_ENTRY_REGEXPR = {
  "2.2" : '<img src="img/elt_19293.png"/><a href="([0-9]+\.html#[\-_0-9A-Za-z]+)"> ([A-Za-z0-9]+)</a>',
  "3.0" : '<img src="img/elt_1470811194701554859.png"/><a href="([0-9]+\.html#[\-_0-9A-Za-z]+)"> ([A-Za-z0-9]+)</a>'
  }
# A map that for each metaclass name return the local url in the metamodel documentation
# This map is computed by reading the index web page of the metamodel.
# A resulting entry is something like "Term" : "15.html#_00080b08-0000-1cb6-0000-000000000000"
# This map is computed on demand and only once
METACLASSNAME_TO_LOCALPAGE_MAP = None

import re
def _getMetaclassNameToLocalPageMap():
  global METACLASSNAME_TO_LOCALPAGE_MAP
  if METACLASSNAME_TO_LOCALPAGE_MAP is None:
    regexpr = METAMODEL_ROOT_ENTRY_REGEXPR[MODELIO_SIMPLE_VERSION]
    html = getWebPage(METAMODEL_INDEX_URL) 
    METACLASSNAME_TO_LOCALPAGE_MAP = {}
    for match in re.findall(regexpr,html):
      (localurl,metaclassname) = match
      METACLASSNAME_TO_LOCALPAGE_MAP[metaclassname] = localurl
  return METACLASSNAME_TO_LOCALPAGE_MAP
  
def getMetaclassMetamodelURL(metaclass,relative=False):
  map = _getMetaclassNameToLocalPageMap()
  metaclassname = getNameFromMetaclass(metaclass)
  if metaclassname is None:
    return None
  else:
    if metaclassname in map:
      url = map[metaclassname]
      if relative:
        return url
      else:
        return MODELIO_METAMODEL_ROOT_URL+"/"+url
    else:
      return None
    

    
def getSubMetaclasses(metaclass):
  """ returns the list of direct subMetaclasses of a metaclass starting 
  """ 
  return METAMODEL_SERVICE.getInheritingMetaclasses(metaclass)


# FIXME does not work with Modelio 3.0
# import inspect
import types
def getSuperMetaclasses(metaclass,inclusive=True):
  """ returns the list of superMetaclass from the parent to Element.
      If inclusive=True includes the metaclass at the beginning
  """
  return [metaclass] if inclusive else []
  # FIXME !!!!
  # ------------------------------------------
  # not executed
  pythonClasses = inspect.getmro(metaclass)
  javaInterfaces = filter( 
                     lambda x:x.isInterface(),
                     excluding(pythonClasses,types.ObjectType))
  metaClasses = filter( 
                lambda x:getNameFromMetaclass(x) is not None and x is not IAdaptable,
                javaInterfaces)
  return metaClasses if inclusive else metaClasses[1:]



def _isSpecialFeature(name): return name in SPECIAL_FEATURES

import java.lang.reflect.Member
import re
def _getJavaMethods(javaclass,inherited=False,regexp=None,argTypes=None,special=False,natives=False):
  """ returns java methods from a metaclass
      regexp : None or a regular expression to filter method names (e.g. "^get|is")
  """   
  javaMethods = javaclass.getMethods() if inherited else javaclass.getDeclaredMethods()
  if not natives:
    # remove methods starting with _ which seems to be natives ones
    # (should be improved using getModifiers instead ...)
    javaMethods = reject(lambda m:m.getName().startswith('-'), javaMethods)
  if regexp is not None:
    javaMethods = filter(lambda m:re.match(regexp,m.getName()), javaMethods) 
  if argTypes is not None:
    javaMethods = filter(lambda m:list(m.getParameterTypes())==list(argTypes), javaMethods)
  if not special:
    javaMethods = reject(lambda m:_isSpecialFeature(m.getName()),javaMethods)
  return javaMethods

import types
from java.util import List as JavaUtilList
from org.eclipse.emf.common.util import EList
if orgVersion:
  from org.modelio.vcore.smkernel import SmList as ModelioList
else:
  from com.modeliosoft.modelio.api.utils import ObList as ModelioList
def isCollectionType(x):
  return x in LIST_TYPES  
LIST_TYPES = [ModelioList,JavaUtilList,types.ListType, EList]    

def _getJavaMethodInfo(javaMethod):
  classe = javaMethod.getDeclaringClass()
  name = javaMethod.getName()
  parameterTypes = list(javaMethod.getParameterTypes())
  returnType = javaMethod.getGenericReturnType()
  if javaMethod.getReturnType() in LIST_TYPES:
    multiple = True
    if len(returnType.getActualTypeArguments()) != 0:
      returnType = returnType.getActualTypeArguments()[0]
    else:
      returnType = javaMethod.getReturnType()[0].getBounds()[0]
  else:
    multiple = False
  return (classe,name,parameterTypes,returnType,multiple)
  # if isinstance(genericreturntype,ParameterizedType):
  #  print "  ","this is a generic type" 
  #  print "  ",returntype.getTypeParameters()[0].getBounds()[0]
  #  if len(genericreturntype.getActualTypeArguments()) != 0:
  #    print "  ",genericreturntype.getActualTypeArguments()[0]      
  
from string import Template
class MetaFeature(object):
  """ MetaFeature are methods of Metaclass.
      To be more precise only the getter/is functions with no parameters are
      selected
  """
  def __init__(self,metaclass,name,type,multiplicity=False):
    self.metaclass = metaclass
    self.name = name
    self.type = type
    self.isAssociationEnd = isMetaclass(self.type)
    self.isEnumeration = isEnumeration(self.type)
    self.multiplicity = multiplicity
  def getMetaclass(self):     return self.metaclass
  def getName(self):          return self.name
  def getType(self):          return self.type
  def isAttribute(self):      return not self.isAssociationEnd
  def isAssociationEnd(self): return self.isAssociationEnd
  def isEnumeration(self):    return self.isEnumeration  
  def isMultiple(self):       return self.multiplicity
  def getSignature(self,ftemplate=None,html=False):
    if ftemplate is None:
      if html:
        ftemplate = "<b>${fname}</b> : <em>${ftype}</em>${fmult}"
      else:
        ftemplate = "${fname} : ${ftype}${fmult}"
    return Template(ftemplate).substitute( \
             mclass=getNameFromMetaclass(self.metaclass),
             fname=self.getName(),
             ftype=getNameFromType(self.type),
             fmult=("[*]" if self.multiplicity else ""))
  def getText(self,ftemplate=None,html=False):
    return self.getSignature(ftemplate,html)
  def __unicode__(self):
    return self.getSignature()
  def __repr__(self):
    return self.getSignature("${mclass}.${fname} : ${ftype}${fmult}")
    
class GetterMetaFeature(MetaFeature):
  def __init__(self,metaclass,name,type,multiplicity=False):
    MetaFeature.__init__(self,metaclass,name,type,multiplicity)
  def eval(self,element):
    try:
      jythonElementMethod=element.__getattribute__(self.name)
      return apply(jythonElementMethod,[])
    except:
      return 'ERROR("cannot apply '+self.name+'")'
      
class FunMetaFeature(MetaFeature):
  def __init__(self,fun,metaclass,name,type,multiplicity=False):
    MetaFeature.__init__(self,metaclass,name,type,multiplicity)    
    self.fun = fun
  def eval(self,element):
    return self.fun(element)
    
def _getMetaFeatureFromJavaMethodInfo(javaMethodInfo):
  (classe,name,parameters,returntype,multiplicty) = javaMethodInfo
  return GetterMetaFeature(classe,name,returntype,multiplicty)

if orgVersion:
  from org.modelio.api.diagram.dg import IDiagramDG
else:
  from com.modeliosoft.modelio.api.diagram.dg import IDiagramDG
FUN_META_FEATURES = {
  "ClassDiagram" : [ \
    ( "DIAGRAMNODE", \
      (lambda d:Modelio.getInstance(). \
                getDiagramService().getDiagramHandle(d).getDiagramNode()), \
      IDiagramDG, \
      False ) ] }
       
def getMetaFeatures(metaclass,inherited=True,groupBySuper=False,additionalFun=[]):
  """ return the meta features of a metaclass, that is MetaFeature created
      for methods getXXX() and isXXX() with no arguments
  """
  # get the signaturex 
  javaMethodInfos = map(_getJavaMethodInfo,
                        _getJavaMethods(metaclass,inherited=inherited,regexp='^(get|is)',argTypes=[]))
  # in method info the parameters are indicated. Here we skip this as we know that
  # the methods do not have parameters.
  metafeatures = map( _getMetaFeatureFromJavaMethodInfo,javaMethodInfos)
  metaclassname = getNameFromMetaclass(metaclass)
  if metaclassname in FUN_META_FEATURES:
    for featuredef in FUN_META_FEATURES[metaclassname]:
      # print "def",featuredef
      (featurename,fun,returntype,multiplicity) = featuredef
      # print "adding ",featurename," returns ",returntype
      metafeatures = metafeatures \
                     + [ FunMetaFeature(fun,metaclass,featurename,returntype,multiplicity)] 
  return metafeatures

class MetaclassInfo(object):
  """ Descriptor of metaclass
  """
  def __init__(self,metaclass):
    self.metaclass = metaclass
    self.metaFeatures = getMetaFeatures(metaclass)
  def getName(self):               return getNameFromMetaclass(self.metaclass)
  def getSuperMetaclasses(self):   return getSuperMetaclasses(self.metaclass)
  def getSubMetaclasses(self):     return getSubMetaclasses(self.metaclass)
  def getMetaFeatures(self):       return self.metaFeatures
  def getSignature(self,mcsigtemplate=None,mcsigsep=" > ",html=False):
    if mcsigtemplate is None:
      mcsigtemplate = "$mcsig"
    s = Template(mcsigtemplate).substitute( \
          mcsig = \
            mcsigsep.join(map(getNameFromMetaclass,self.getSuperMetaclasses())) )   
    return unicode(s)
  def __repr__(self):
    return self.getSignature()
  def __unicode__(self):
    return self.getName()
  def getBody(self,fsep=None,ftemplate=None,html=False):
    if fsep is None:
      fsep="<br/>" if html else "\n"
    return fsep.join( \
              [ feature.getSignature(ftemplate=ftemplate,html=html) \
                  for feature in self.getMetaFeatures() ]  )
  def getText(self,mctemplate=None,mcsigtemplate=None,ftemplate=None,fsep=None,html=False):
    if mctemplate is None:
      if html:
        mctemplate = "$mcsig<br/>$mcbody"
      else:
        mctemplate = "$mcsig\n$mcbody"
    s = Template(mctemplate).substitute( \
          mcsig = self.getSignature(mcsigtemplate=mcsigtemplate,html=html),
          mcbody = self.getBody(ftemplate=ftemplate,fsep=fsep,html=html))
    return unicode(s)

# print getMetaclassInfo(IUseCase).getText( \
#   fsep="\n",ftemplate="  $fname",mctemplate="class $mcsig {\n$mcbody\n}")  

METACLASS_INFOS = dict()

def getMetaclassInfo(metaclass):  
  name = getNameFromMetaclass(metaclass)
  if name in METACLASS_INFOS:
    return  METACLASS_INFOS[name]
  else:
    info = MetaclassInfo(metaclass)
    METACLASS_INFOS[name] = info
    return info

# this list comes from the modelio script ExportDiagrams.py, function getFullName

PARENT_FEATURES = {
    "ModelTree"       : "getOwner",
    "Behavior"        : "getOwner",
    "BpmnRootElement" : "getOwner",
    "Feature"         : "getOwner",
    "AbstractDiagram" : "getOrigin",
    "BpmnFlowElement" : "getContainer"
  }
  
def getElementParent(element):
  """ return the parent of an element, the notion of parent being defined by 
      PARENT_FEATURES
  """
  for metaclassName in PARENT_FEATURES.keys():
    methodName=PARENT_FEATURES[metaclassName]
    metaclass = getMetaclassFromName(metaclassName)
    if isinstance(element,metaclass):
      return apply(element.__getattribute__(methodName),[])    
  return None
  
def _getElementParents(element):
  parent = getElementParent(element)
  if parent is None: 
    return []
  else:
    return [parent]+_getElementParents(parent)

def getElementParents(element,inclusive=False,reverse=False):
  parents = ([element] if inclusive else [])+_getElementParents(element)
  return reversed(parents) if reverse else parents

def getElementPath(element):
  """ return a qualified name for the element if it is possible to compute one
      by concatenating the "name" of parent elements.
      The path is computed according to some appropriate
      "parentship" association depending on the type of elements.
      If it is not possible to get the path, then return the id of the element.
  """
  try:
    names = map( lambda x:x.getName(), 
                 getElementParents(element,inclusive=True,reverse=True))
    if exists(isEmpty,names):
      return unicode(getElementId(element))
    else:
      return unicode(".".join(names))
  except:
    return unicode(getElementId(element))  
    
    
    
#--------- model level ------------------------------------------ 

def isNone(x):
  return x is None
  
def isScalar(x):
  return    isinstance(x,basestring) \
         or isinstance(x,int) \
         or isinstance(x,bool) \
         or isinstance(x,long) \
         or isinstance(x,float)

def isEnumerationLiteral(x):
  return isinstance(x,java.lang.Enum)
  
def isAtomic(x):
  return isScalar(x) or isEnumerationLiteral(x)
  
def isElement(x):
  """ True for objects XXX
  """
  return isinstance(x,ModelioElement) \
         or (x is not None \
             and not isAtomic(x) \
             and not isElementList(x))         
           
def isElementList(x):
  return isList(x) and forAll(isElement,x)
  


def getElementId(element):
  try:
    s = u"ID("+unicode(element.getIdentifier())+u")"
  except:
    try:
      s = unicode(element.getId())
    except: 
      s = u"id("+unicode(id(element))+u")"  
  return s

from java.util import List as JavaList

def getElementNameOrId(element,unnamed=None):
  try:
    s = element.getName()
  except:
    s = None
  if s is None or len(s)==0 :
    if unnamed is None:
      s = getElementId(element)
    else:
      s = unnamed
  return unicode(s)


def getElementSignature(element,unnamed=None):
  """ function to transform an individual element to some text text"
      This function is used in ModelValue class
  """
  return getElementNameOrId(element,unnamed=unnamed) \
         +" : "+ getNameFromMetaclass(getMetaclass(element))

    

class ModelValue(object):
  def __unicode__(self):  return unicode(self.getText())
  # isScalar()
  # getValue()
  # getKind()
  # getText()
  # isElementContainer()
  # isScalar()
  # isAtomic()
  # isEnumerationLiteral()
  # isScalar()
  # isElement()
  # isElementList()
  # isEmpty()
  def notEmpty(self):                 return not self.isEmpty()
  
class ElementContainerModelValue(ModelValue):
  # isEmpty()
  # notEmpty()
  # getCard()
  # isMultiple()
  def isElementContainer(self):       return True
  def isEnumerationLiteral(self):     return False
  def isScalar(self):                 return False
  def isAtomic(self):                 return False
  
class NoneModelValue(ElementContainerModelValue):
  def getValue(self):                 return None
  def getKind(self):                  return "element"
  def isElement(self):                return True
  def isElementList(self):            return False
  def getCard(self):                  return 0
  def isMultiple(self):               return False
  def isEmpty(self):                  return True
  def getText(self):                  return "None"
  
class ElementModelValue(ElementContainerModelValue):
  def __init__(self,element):          
    self.element = element    
  def getValue(self):                 return self.element
  def getKind(self):                  return "element"
  def isElement(self):                return True
  def isElementList(self):            return False
  def getCard(self):                  return 1
  def isMultiple(self):               return False
  def isEmpty(self):                  return False
  def getText(self):                  
    return "\n    "+getElementSignature(self.element)

class ElementListModelValue(ElementContainerModelValue):
  def __init__(self,elementList):          
    self.elementList = elementList    
  def getValue(self):                 return self.elementList
  def getKind(self):                  return "elementList"
  def isElement(self):                return False
  def isElementList(self):            return True
  def getCard(self):                  return len(self.elementList)
  def isMultiple(self):               return True
  def isEmpty(self):                  return self.getCard() == 0
  def getText(self):                  
    return "\n    "+"\n    ".join(map(getElementSignature,self.elementList))
  
class AtomicModelValue(ModelValue):
  def isElementContainer(self):       return False
  def isElement(self):                return False
  def isElementList(self):            return False
  def isAtomic(self):                 return True
  def isEmpty(self):                  return False
  
class EnumerationLiteralModelValue(AtomicModelValue):
  def __init__(self,literal):     
    self.literal = literal
  def getValue(self):                 return self.literal
  def getKind(self):                  return "enumerationLiteral"
  def getText(self):                  return self.literal.toString()
  def isScalar(self):                 return False

class ScalarModelValue(AtomicModelValue):
  def __init__(self,scalar):          self.scalar = scalar
  def getKind(self):                  return "scalar"
  def getText(self):                  return unicode(self.scalar)
  def isScalar(self):                 return True
  
class StringModelValue(ScalarModelValue):
  def __init__(self,string):
    self.string = string
  def getValue(self):                 return self.string
  def getText(self):                  return u'"'+self.string+'"'

  

  
def getModelValueFromValue(value):
  if isNone(value):
    return NoneModelValue()
  if isString(value):
    return StringModelValue(value)
  elif isEnumerationLiteral(value):
    return EnumerationLiteralModelValue(value)
  elif isScalar(value):
    return ScalarModelValue(value)
  elif isElementList(value):
    return ElementListModelValue(value)
  elif isElement(value):
    return ElementModelValue(value)
  else: 
    print "getModelValueFromValue(",value,"): The parameter type is not recognized",type(value)
    return StringModelValue("UNKNOWN, see the console")

  
  
  
  
  
#--------- introspection at the model/metamodel level ----------

if orgVersion:
  from org.modelio.api.diagram import IDiagramGraphic  
else:
  from com.modeliosoft.modelio.api.diagram import IDiagramGraphic



def getMetaclass(element):
  """ returns the metaclass of the given element
  """
  # XXX TODO check
  if isinstance(element,ModelioElement):
    if orgVersion:
      name = element.getMClass().getName()
    else:
      name = element.metaclassName
    return getMetaclassFromName(name)
  else:
    return type(element)
  
def getAllInstances(metaclass):
  """ returns all instances of a given metaclass
  """
  return MODELING_SESSION.findByClass(metaclass)

def getSelectedInstances(metaclass,attributeName,attributeValue):
  """ returns all instances with a value for a given attribute
  """
  return MODELING_SESSION.findByAtt(metaclass)
  
def getModelRoot():
  return MODELING_SESSION.getModel()



    

class MetaFeatureSlot(object):
  """ MetaFeature slots are values of a given feature for given element
  """
  def __init__(self,element,metafeature):
    self.metaFeature = metafeature
    self.element = element
    # computed on demand
    self.modelValue     = None
  def getElement(self):        return self.element
  def getMetaFeature(self):    return self.metaFeature
  def getName(self):           return self.metaFeature.getName()
  def getModelValue(self):
    if self.modelValue is None:
      self.modelValue = getModelValueFromValue(self.metaFeature.eval(self.element))
    return self.modelValue
  def isEmpty(self):
    return self.getModelValue().isEmpty()
  def notEmpty(self):
    return not self.isEmpty()
  def getCard(self):
    return self.getModelValue().getCard()
  def getText(self,stemplate=None,ftemplate=None,mvtemplate=None):
    if stemplate is None:
      stemplate = "$fsig = $mv"
    mval = self.getModelValue()
    fsig = self.getMetaFeature().getText(ftemplate=ftemplate)
    mvaltext = mval.getText()
    # s = Template(stemplate).substitute( \
           # fsig = self.getMetaFeature().getText(ftemplate=ftemplate),
           # mv = mval.getText(mvtemplate=mvtemplate),
           # mvscalar = mvaltext if mval.isScalar() else ""
           # mvenum = mvaltext if mval.isEnumerationLiteral() else ""
           # mvelement = mvaltext if mval.isE
           # mvtype = unicode(type(self.getModelValue().getValue())) )
    s = fsig+" = "+mvaltext
    return unicode(s)
  def __unicode__(self):
    return unicode(self.metaFeature.getSignature()+" = "+unicode(self.getModelValue()))
  def __repr__(self):
    return self.getText()
  
    
  # TODO we should probably define equals or something like that
    
def getMetaFeatureSlots(element,inherited=True):
  metaclass = getMetaclass(element)
  return [MetaFeatureSlot(element,feature) for feature in getMetaFeatures(metaclass)]
  
  
class ElementInfo(object):
  """
  """
  def __init__(self,element):
    self.element = element
    self.identifier = id(element) # TODO self.element.getIdentifier()
    self.metaclass = getMetaclass(element)
    self.metaclassName = getNameFromMetaclass(self.metaclass)
    self.metaclassInfo = getMetaclassInfo(self.metaclass)
    self.name = getElementNameOrId(self.element)
    self.path = getElementPath(element)
    # the slot list keep the order corresponding to inheritance
    # it is computed on demande
    self.slotList = None
    # the slot map is indexed by slot names. It is computed on demand
    self.slotMap = None
  def getElement(self):          return self.element
  def getName(self):             return self.name
  def getPath(self):             return self.path
  def getMetaclass(self):        return self.metaclass
  def getMetaclassName(self):    return self.metaclassName
  def getMetaclassInfo(self):    return self.metaclassInfo
  def _getSlotList(self):
    # compute the slot list on demand
    if self.slotList is None:
      self.slotList = getMetaFeatureSlots(self.element)
    return self.slotList
  def getSlotList(self,emptySlots=True):
    slots = self._getSlotList()
    if not emptySlots:
      slots = reject(MetaFeatureSlot.isEmpty,slots)
    return slots      
  def getSlotMap(self):
    if self.slotMap is None:
      slots = self.getSlotList()
      self.slotMap = {}
      for slot in slots:
        self.slotMap[slot.getName()] = slot 
    return self.slotMap
  def getSlot(self,name):
    return self.getSlotMap()[name]
  def getModelValue(self,name):
    return self.getSlot(name).getModelValue()
  def getSignature(self,path=True):
    return (self.path if path else self.name) \
           + " : "+self.metaclassInfo.getSignature()
  def getText(self,emptySlots=False):
    return u'\n'.join( \
          [self.getSignature()] \
        + [u"  "+slot.__repr__() \
             for slot in self.getSlotList(emptySlots) ]
      )
  def __unicode__(self):
    return  str(self.element.getName())+" : "+self.metaclassName
  def __repr__(self):
    return self.getSignature(True)

    
ELEMENT_INFOS = dict()

# def getElementInfo(element):
  # XXX TODO the idenfier was a good solution, fund anotuer one
  # """ return for an element its description (ElementInfo)
  # """  
  # try :
    # i = element.getIdentifier()
  # except:
    # i = id(element)
  # if i in ELEMENT_INFOS:
    # return  ELEMENT_INFOS[i]
  # else:
    # info = ElementInfo(element)
    # ELEMENT_INFOS[i] = info
    # return info

def getElementInfo(element):
    info = ElementInfo(element)
    return info    
    
    
def show(x,html=False):
  if isElement(x):
    print getElementInfo(x).getText()
  elif isMetaclass(x):
    if html:
      ftempl = "<li>${mclass}.<b>${fname}</b> : <em>${ftype}</em>${fmult}</li>"
      fsep = ""
      mctempl = "<h3>$mcsig</h3><ul>$mcbody</ul>"
      html = getMetaclassInfo(x).getText(html=True,ftemplate=ftempl,mctemplate=mctempl,fsep="")
      HtmlWindow(html,width=600,height=800)
    else:
      print getMetaclassInfo(x).getText(html=html)
  elif isList(x):
    for item in x:
      show(item)
  else:
    print x

import os    
from org.eclipse.swt.graphics import Color, Image
from org.eclipse.swt.widgets import Display
DEVICE = Display.getCurrent() # Modelio.getInstance().getImageService().getMetaclassImage(Package).getDevice()
RESOURCE_PATH = os.path.join(os.path.dirname(__file__),'res')

class NavigatorImageProvider(object):
  def __init__(self,resourcePath):
    self.imageMap = {}
    for name in ["atomic","assoc-1","assoc-n"]:
    # ,"integer","float","long","boolean","enumeration"]
      self.imageMap[name] = Image(DEVICE,os.path.join(resourcePath,name+".gif"))
  def getImage(self,name):
    if name in self.imageMap:
      return self.imageMap[name]
    else:
      return None    
NAVIGATOR_IMAGE_PROVIDER=NavigatorImageProvider(RESOURCE_PATH)

def elementTree(x,emptySlots=False):
  def _getChildren(data):
    if isinstance(data,ElementInfo):
      return data.getSlotList(emptySlots=emptySlots)
    elif isinstance(data,MetaFeatureSlot):
      mv = data.getModelValue()
      if mv.isElement():
        return [ getElementInfo(mv.getValue()) ]
      elif mv.isElementList():
        return map(getElementInfo,mv.getValue())
      else:
        return []        
  def _isLeaf(data):
    if isinstance(data,ElementInfo):
      return False
    elif isinstance(data,MetaFeatureSlot):
      mv = data.getModelValue()
      if mv.isElement():
        return False
      elif mv.isElementList():
        return False
      else:
        return True
  def _getText(data):
    if isinstance(data,ElementInfo):
      return data.getSignature()
    elif isinstance(data,MetaFeatureSlot):
      mv = data.getModelValue()
      if mv.isAtomic():
        return data.getText()
      elif mv.isElementContainer():
        return data.getMetaFeature().getSignature()+" = ["+str(data.getCard())+"]"
      else:
        return "???"+unicode(mv)
  def _getImage(data):
    if isinstance(data,ElementInfo):
      return getMetaclassImage(data.getMetaclass())
    elif isinstance(data,MetaFeatureSlot):
      mv = data.getModelValue()
      if mv.isElement():
        return NAVIGATOR_IMAGE_PROVIDER.getImage("assoc-1")
      elif mv.isElementList():
        return NAVIGATOR_IMAGE_PROVIDER.getImage("assoc-n")
      else:
        return NAVIGATOR_IMAGE_PROVIDER.getImage("atomic")
  def _getGrayed(data):
    if isinstance(data,ElementInfo):
      return False
    else:
      return True  
  def _getForeground(data):
    if isinstance(data,ElementInfo):
      return Color(Display.getCurrent(),0,0,150)
    else:
      return Color(Display.getCurrent(),0,150,0)    
  if not isList(x):
    x = [x]
  TreeWindow(map(getElementInfo,x),_getChildren,_isLeaf, \
                 getTextFun=_getText,getImageFun=_getImage, \
                 getGrayedFun=_getGrayed, \
                 getForegroundFun=_getForeground,
                 title = "Model/Metamodel CoExplorer")

#----------------------------------------

NAVIGATION_SERVICE = Modelio.getInstance().getNavigationService()
def navigateToElement(element):
  NAVIGATION_SERVICE.fireNavigate(element)
                  


                  
                  
                  
print "module introspection loaded from",__file__
