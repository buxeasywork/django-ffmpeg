# Create your views here.
import os
import subprocess
import shlex
import pickle

from django.template import Context, Template, loader, RequestContext
from django.http import HttpResponse, Http404
from django import forms
from django.conf import settings
from django.core.servers.basehttp import FileWrapper
import threading

from random import choice
import string

TEMP_PATH = getattr(settings, 'VIDCONVERT_TEMP_PATH',os.path.join(settings.MEDIA_ROOT, 'TEMP'))

if not os.path.exists(TEMP_PATH):
    os.makedirs(TEMP_PATH)

# Look for user function to define file paths
VID_PATH = getattr(settings, 'VIDCONVERT_PATH', os.path.join(settings.MEDIA_ROOT, 'vids'))

if not os.path.exists(VID_PATH):
    os.makedirs(VID_PATH)

def random_string(length=8, chars=string.letters + string.digits):
    return ''.join([choice(chars) for i in range(length)])
    
class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file  = forms.FileField()

class Converter:
    def __init__(self, request_file):
        self.identifer = random_string()
        self.temp_path = TEMP_PATH
        
        ext = os.path.splitext(request_file.name)[1]
        
        self.temp_file_path = os.path.join(self.temp_path, self.identifer + '.flv')        
        
        self.input_file_path = os.path.join(VID_PATH,  self.identifer + ext)
        self.output_file_path = os.path.join(VID_PATH, self.identifer + '.flv')
        self.poster_frame_path = os.path.join(VID_PATH, self.identifer + '.jpg')
        self.request_file = request_file
        
        self.do_upload()
        self.do_poster_frame()
        self.do_convert()
    
    def do_upload(self):
            destination = open(self.input_file_path, 'wb+')
            for chunk in self.request_file.chunks():
                destination.write(chunk)
            destination.close()
            
    def do_poster_frame(self):
        c = 'ffmpeg -i '+str(self.input_file_path)+' -ss 00:00:01 -vcodec mjpeg -vframes 1 -f image2 '
        c +=  str(self.poster_frame_path)
        args = shlex.split(c)
        subprocess.call(args)
        
        
    def do_convert(self):
        c = '\'/usr/local/bin/ffmpeg -i '+ str(self.input_file_path)
        c+=' -acodec libfaac -ab 128k -ac 2 -ar 22050 -vcodec libx264 -vpre default -crf 22 -threads 0 '
        c+= self.temp_file_path +';'
        c+='mv ' + self.temp_file_path + ' ' 
        c+= self.output_file_path + '\''
        print c
        #r = os.system(c)
        args = shlex.split(c)
        subprocess.Popen(args, close_fds=True, shell=True)   
        
class Movie():
    def __init__(self, id):
        self.id = id
        
    def video_url(self):
        return '/vids/get/' + self.id
     
    def poster_frame_url(self):
        return '/vids/poster_frame/' + self.id
    
    def local_url(self, ext):
        return os.path.join(settings.MEDIA_URL,'vids',self.id+ext)
        
def movies(request):
    ids = []
    for x in os.listdir(VID_PATH):
        if (x.lower().endswith('.flv')):
            ids.append(Movie(x[:-4]))
    print ids
    
    t = loader.get_template('movies.django')
    
    return HttpResponse(t.render(Context({'movies':ids})))               
            
def status(request, id):
    path = os.path.join(VID_PATH, id +".flv")
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
    
    output_path = dir = os.path.join(VID_PATH, id+'.jpg')     
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
            rname = Converter(request.FILES['file'])
            #MovieInfo(request.FILES['file'], rname)             
    return HttpResponse(rname.identifer)

def get_video(request, id):
    path = os.path.join(VID_PATH, id+'.flv')
    #path = os.path.join(dir, id+'.flv')
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