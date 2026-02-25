from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import requests
import json

EXECUTOR_HTTP_URL = "http://executor:8080/run"

def codeedit(request):
    return render(request, "playground/codeedit.html", {"title": "Среда разработки"})

def runcode(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method Not Allowed"}, status=405)

    try:
        payload = json.loads(request.body)
        code = payload.get("code", "")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        resp = requests.post(EXECUTOR_HTTP_URL, json={"code": code}, timeout=5)
        resp.raise_for_status()
        try:
            data = resp.json()
        except ValueError:
            return JsonResponse({"error": "Executor вернул не JSON", "raw": resp.text}, status=502)

        return JsonResponse(data)

    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"Executor connection error: {str(e)}"}, status=502)

