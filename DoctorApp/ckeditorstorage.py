from django.core.files.storage import FileSystemStorage

class CKEditorStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        kwargs['location'] = 'media/uploads/ckeditor/'  
        kwargs['base_url'] = '/media/uploads/ckeditor/' 
        super().__init__(*args, **kwargs)
