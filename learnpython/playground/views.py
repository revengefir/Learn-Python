from django.shortcuts import render
from django.http import HttpResponse
import traceback
from io import StringIO
from contextlib import redirect_stdout

def execute_code(code):
    try: 
        output_buffer = StringIO()
        with redirect_stdout(output_buffer):
            exec(code)
        output = output_buffer.getvalue()
    except Exception as e:
        output = f"Error: {str(e)} \n {traceback.format_exc()}"
    return output

def index(request):
    return render(request, 'editcode.html')

def runcode(request):
    if request.method == "POST":
        codeareadata =  request.POST['codearea']
        output = execute_code(codeareadata)
        return render(request, 'index.html', {"code": codeareadata, "output": output})
    else:
        return HttpResponse("Method not allowed", status = 405)

