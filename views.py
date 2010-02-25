# Create your views here.
import os
import subprocess
import shlex

from django.template import Context, Template, loader, RequestContext
from django.http import HttpResponse, Http404
from django import forms
from django.conf import settings
from django.core.servers.basehttp import FileWrapper
import threading

from random import choice
import string

def random_string(length=8, chars=string.letters + string.digits):
    return ''.join([choice(chars) for i in range(length)])
    
class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file  = forms.FileField()

threads = {}

class ConvertThread(threading.Thread):
    def __init__(self, filename, ext):
        threading.Thread.__init__(self)
        dir = os.path.join(settings.MEDIA_ROOT, 'TEMP')
        self.filename = os.path.join(dir,filename)
        self.ext = ext
        
    def run(self):
        #print(self.filename)   
        c = '/usr/local/bin/ffmpeg -i '+ str(self.filename)+str(self.ext)
        c+=' -acodec libfaac -ab 128k -ac 2 -ar 22050 -vcodec libx264 -vpre default -crf 22 -threads 0 '
        c+=str(self.filename)+'.flv'
        print c
        #r = os.system(c)
        args = shlex.split(c)
        subprocess.Popen(args, close_fds=True)    
        #if (r):
        #    print 'no good?' 
        #print 'convert complete'
    
def handle_upload_file(f):
    dir = os.path.join(settings.MEDIA_ROOT, 'TEMP')
    dir2 = os.path.join(dir,'IN_PROGRESS')
    if not os.path.exists(dir2):
        os.makedirs(dir2)
    
    fname = os.path.splitext(f.name)[0]
    ext = os.path.splitext(f.name)[1]
    rname = random_string()
    
    path = os.path.join(dir, rname+ext)
    destination = open(path, 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()
    
    c = '\'/usr/local/bin/ffmpeg -i '+ str(path)
    c+=' -acodec libfaac -ab 128k -ac 2 -ar 22050 -vcodec libx264 -vpre default -crf 22 -threads 0 '
    c+=os.path.join(dir,'IN_PROGRESS', rname) + '.flv;'
    c+='mv ' + os.path.join(dir,'IN_PROGRESS', rname) + '.flv '
    c+= os.path.join(dir, rname + '.flv') + '\''
    print c
    #r = os.system(c)
    args = shlex.split(c)
    subprocess.Popen(args, close_fds=True, shell=True)    
        
    return rname

def status(request, id):
    path = os.path.join(settings.MEDIA_ROOT, 'TEMP', id +".flv")
    in_progress_path =  os.path.join(settings.MEDIA_ROOT, 'TEMP', "IN_PROGRESS", id +".flv")
    if os.path.exists(path):
        return HttpResponse("COMPLETE")
    elif os.path.exists(in_progress_path):
        return HttpResponse("IN PROGRESS")
    
    return HttpResponse("NOT FOUND")
    #t = loader.get_template('status.django')
    #return HttpResponse(t.render(Context({
    #                                      })))

def poster_frame(request, id):
    input_path = os.path.join(settings.MEDIA_ROOT, 'TEMP',id+'.flv')
    output_path = dir = os.path.join(settings.MEDIA_ROOT, 'TEMP', id+'.jpg') 
    c = 'ffmpeg -i '+str(input_path)+' -ss 00:00:01 -vcodec mjpeg -vframes 1 -f image2 ' + str(output_path)
    args = shlex.split(c)
    subprocess.call(args)
    if (os.path.exists(output_path)):
        wrapper = FileWrapper(file(output_path))
        response = HttpResponse(wrapper, content_type='image/jpeg')
        response['Content-Disposition'] = 'attachment; filename='+id+'.jpg'
        response['Content-Length'] = os.path.getsize(output_path)
        return response
    raise Http404
        
    

def convert_video(request):
    rname = 'FORM FAIL'
    if request.method =='POST': 
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid(): 
            rname = handle_upload_file(request.FILES['file'])            
    return HttpResponse(rname)

def get_video(request, id):
    dir = os.path.join(settings.MEDIA_ROOT, 'TEMP')
    path = os.path.join(dir, id+'.flv')
    if (os.path.exists(path)):
        wrapper = FileWrapper(file(path))
        response = HttpResponse(wrapper, content_type='video/x-flv')
        response['Content-Disposition'] = 'attachment; filename=test.flv'
        response['Content-Length'] = os.path.getsize(path)
        return response
            
    raise Http404

def convert_video_form(request):
    t = loader.get_template('convert_form.django')
    return HttpResponse(t.render(Context(
                                         {'form': UploadFileForm()
                                          })))