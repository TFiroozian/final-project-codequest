FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt ./

RUN python3.12 -m pip install -r requirements.txt -t .

COPY common ./common
COPY ingestion ./ingestion

CMD ["ingestion.app.lambda_handler"]