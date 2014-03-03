import os,subprocess
import datetime
import threading
import re

from resources.lib.xbmcguie.xbmcContainer import *
from resources.lib.xbmcguie.xbmcControl import *
from resources.lib.xbmcguie.tag import Tag
from resources.lib.xbmcguie.category import Category,Setting

from resources.lib.xbianconfig import xbianConfig
from resources.lib.utils import *

import resources.lib.translation
_ = resources.lib.translation.language.ugettext


import xbmcgui,xbmc

CFGFILE = '/etc/xbian-a2dp.conf'

def getConfigValue(key):   
     with open(CFGFILE,'r') as f :             
         mat = filter(lambda x : re.match('%s=([^ ]+).*'%key,x),f.readlines())            
     if mat :                     
         return mat[0].split('=')[1].split(' ')[0].replace('\n','')
     return 0
         
def setConfigValue(key,value):
     with open(CFGFILE,'r') as f :             
         mat = filter(lambda x : re.match('%s=([^ ]+).*'%key,x),f.readlines())
     if mat :
         #replace
         def replace(x) :
             print x
             if re.match('%s=([^ ]+).*'%key,x) :                    
                 return re.sub('%s=([^ ]+).*'%key,'%s=%s\n'%(key,value),x,1)
             else :
                 return x
         with open(CFGFILE, "r") as f:                
             data = map(replace,open(CFGFILE,'r').readlines())
         with open(CFGFILE, "w") as f:                
             f.writelines(data) 
     elif value in ('0','1'):
         with open(CFGFILE, "a") as f:
             f.write('%s=%s\n'%(key,value))                
     else :
         return False
     return True

RPI_AUDIO_OUTPUT = ['Auto','Analog','Hdmi']

class bluetooth_label(Setting) :
    CONTROL = CategoryLabelControl(Tag('label','Bluetooth'))

class bt_pairing(MultiSettingControl):
    LABEL = 'Auto Pairing'

    def onInit(self) :
        self.autopairing = RadioButtonControl(Tag('label',self.LABEL))
        self.addControl(self.autopairing)
        self.multitimeout = MultiSettingControl(Tag('visible','! SubString(Control.GetLabel(%d),*)'%self.autopairing .getId()))
        self.timeout = ButtonControl(Tag('label','     -Visibility timeout (sec)'))
        self.timeout.onClick = lambda count: self.timeout.setValue(getNumeric('Discovery Timeout',self.timeout.getValue(),1,1000))
        self.multitimeout.addControl(self.timeout)
        self.addControl(self.multitimeout)

    def getValue(self) :     
        rc =self.autopairing.getValue()
        print rc
        if rc :
            return ['0']
        else :
            return ['1',self.timeout.getValue()]

    def setValue(self,value) :       
        self.autopairing.setValue(value[0])
        if not value[0] :
            self.timeout.setValue(value[1])


class bt_pairing_gui(Setting) :
    CONTROL = bt_pairing()
    DIALOGHEADER = 'Bluetooth pairing'        
    SAVEMODE = Setting.ONUNFOCUS


    def setControlValue(self,value) :
        if value[0] == '1' :
            self.control.setValue([False,value[1]])
        else :
            self.control.setValue([True])
        
    def getUserValue(self):
        return self.control.getValue()

    def getXbianValue(self):
        rc = getConfigValue('PAIREDMODE')
        print 'paired',rc
        if rc != '0' :
            print rc,getConfigValue('DELAY')
            return['1',getConfigValue('DELAY')]
        else :            
            return ['0']

    def setXbianValue(self,value):
        setConfigValue('PAIREDMODE',value[0])
        if value[0] != '0' :
            setConfigValue('DELAY',value[1])
            xbianConfig('services','stop','bluetooth-pairing')
        else :
			xbianConfig('services','start','bluetooth-pairing')
        return True 

class bt_pin(Setting) :
    CONTROL = ButtonControl(Tag('label','Pin code'))
    DIALOGHEADER = 'Bluetooth pin code'
        
    def getUserValue(self):
        return getNumeric('Pin Code',self.control.getValue(),0,9999)

    def getXbianValue(self):
        return str(getConfigValue('PIN'))

    def setXbianValue(self,value):
        setConfigValue('PIN',value)
        xbianConfig('services','restart','bluetooth-pairing')
        return True


class bt_stop_xbmc(Setting) :
    CONTROL = RadioButtonControl(Tag('label','Stop xbmc player when a2dp connection'))
    DIALOGHEADER = 'Stop xbmc when a2dp incoming'
    
    def setControlValue(self,value) :
        if value == '1' :
            value = True
        else :
            value = False
        self.control.setValue(value)
        
    def getUserValue(self):
        return str(self.control.getValue())

    def getXbianValue(self):
        return getConfigValue('XBMCPLAYERPSTOP')

    def setXbianValue(self,value):
        setConfigValue('XBMCPLAYERPSTOP',value)
        return True
        
class rpi_audio_output(Setting) :    
    CONTROL = SpinControlex(Tag('label','Audio alsa output'))
    DIALOGHEADER = 'Audio Alsa Output'    
    SAVEMODE = Setting.ONUNFOCUS
    
    def onInit(self):
        for output in RPI_AUDIO_OUTPUT :        
            content = Content(Tag('label',output),defaultSKin=False)
            self.control.addContent(content)
    
    def getUserValue(self):
        return self.control.getValue()

    def getXbianValue(self):        
        return RPI_AUDIO_OUTPUT[int(getConfigValue('ALSAOUTPUT'))]

    def setXbianValue(self,value):
        setConfigValue('ALSAOUTPUT',RPI_AUDIO_OUTPUT.index(value))
        return True

class bluetooth(Category) :
    TITLE = 'Bluetooth'
    SETTINGS = [bluetooth_label,bt_pairing_gui,rpi_audio_output,bt_stop_xbmc]
