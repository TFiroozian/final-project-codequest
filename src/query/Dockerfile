FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt ./

RUN python3.12 -m pip install -r requirements.txt -t .

COPY query ./query
COPY common ./common

CMD ["query.app.lambda_handler"]