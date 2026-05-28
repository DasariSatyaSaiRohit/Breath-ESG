from django.urls import path
from .views import UtilityUploadView, TravelPullView, SapCsvUploadView,TravelUploadView, JobDetailView
# from .viewers.sap_upload import SapCsvUploadView

urlpatterns = [
    path("utility/upload/", UtilityUploadView.as_view(), name="utility-upload"),
    path("travel/pull/", TravelPullView.as_view(), name="travel-pull"),
    path("travel/upload/", TravelUploadView.as_view(), name="travel-upload"),
    path("sap/upload/", SapCsvUploadView.as_view(), name="sap-upload"),
    path("jobs/<uuid:pk>/", JobDetailView.as_view(), name="job-detail"),
]
