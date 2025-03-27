from rest_framework.response import Response
from rest_framework import status


class CustomResponse:
    @staticmethod
    def success(data=None, status_code=status.HTTP_200_OK):
        return Response({
            "success": True,
            "status":status_code,
            "data": data
        })

    @staticmethod
    def error(message="Error", status_code=status.HTTP_400_BAD_REQUEST):
        return Response({
            "success": False,
            "status":status_code,
            "message": message,
        })