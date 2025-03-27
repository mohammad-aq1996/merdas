from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.exceptions import APIException
from core.response import CustomResponse


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return CustomResponse.error(
            message=str(exc),
            status_code=response.status_code
        )

    return CustomResponse.error(
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


class BadRequestException(APIException):
    status_code = 400
    default_detail = 'Bad request'
    default_code = 'bad_request'


class NotFoundException(APIException):
    status_code = 404
    default_detail = 'Not found'
    default_code = 'not_found'