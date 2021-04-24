# pylint: disable-all

import psycopg2
import json

class DbUtils:

    @staticmethod
    def insert_into_table(request):
        print("Init Insert data into table")
        conn = psycopg2.connect(database="project", user="postgres", password="postgres", host="127.0.0.1", port="5432")
        request_params_json = None
        print("Opened db and Connection created successfully")
        cur = conn.cursor()

        try:
            print("Requests :")
            print(request.url,request.path,request.body,request.method,request.querystring,request.params,
                  request.headers,request.response)

            request_params_json = json.dumps(request.params)
            print("request params json" + request_params_json)

            request_headers_json = json.dumps(dict(request.headers))
            print("request headers json" + request_headers_json)

            print("Printing request response")
            print(request.response.reason)
            print(request.response.status_code)
            print(type(request.response.status_code))

            print(type(request.body))
            request_body_json = json.dumps(request.body.decode('utf-8'))

            cur.execute("""
                        INSERT INTO public.request (request_url, request_path, request_method, request_queryString, 
                        request_params, request_headers, response_reason, response_status, request_body) 
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id;
                        """,
                        (request.url,request.path,request.method,request.querystring,request_params_json,
                         request_headers_json, request.response.reason, request.response.status_code, request_body_json))
            print("Request executed successfully")
            last_id = cur.fetchone()[0]

            print("Request id", last_id)

            response_headers_json = json.dumps(dict(request.response.headers))
            print("response headers json" + request_headers_json)

            response_body_json = json.dumps(request.response.body.decode('utf-8'))

            cur.execute("""
                        INSERT INTO public.response (request_id, response_reason, response_statuscode, response_headers, 
                        response_body) 
                        VALUES (%s, %s,%s,%s,%s);
                        """,
                        (last_id, request.response.reason, request.response.status_code, response_headers_json,
                         response_body_json))
            print("Response executed successfully")
            conn.commit()
            print("Records Inserted successfully")
            conn.close()

        except Exception as exp:
            print("Got exception %s", (exp))
            conn.rollback()
            print("Change not committed")
            conn.close()
        return;

    @staticmethod
    def print_request(request):
        print(
            request,
            request.url,
            request.path,
            request.body,
            request.method,
            request.querystring,
            request.params,
            request.headers,
            request.response
        )
        return;

    @staticmethod
    def print_response(response):
        print(
            response.status_code,

            response.reason,
            response.headers,
            response.body
        )
        return;

    @staticmethod
    def interceptor(request, response):
        print(request.url)

        if 'detectportal.firefox.com' in request.url:
            print("Request Intercepted")
            Driver.print_request(request)
            Driver.print_response(response)
            Driver.insert_into_table(request)
            Driver.mock_server(request)

    @staticmethod
    def mock_server(request):
        print("Init Mock server")
        conn = psycopg2.connect(database="project", user="postgres", password="postgres", host="127.0.0.1", port="5432")
        request_params_json = None
        print("Opened db and Connection created successfully")
        cur = conn.cursor()

        try:
            request_params_json = json.dumps(request.params)
            print("request params json" + request_params_json)

            request_headers_json = json.dumps(dict(request.headers))
            print("request headers json" + request_headers_json)

            request_body_json = json.dumps(request.body.decode('utf-8'))

            cur.execute("""
                        SELECT id from public.request WHERE request_url like %s AND
                        request_method like %s AND request_headers like %s AND
                        request_body like %s
                        """,
                        (request.url, request.method, request_headers_json, request_body_json))
            print("Selection from request executed successfully")
            last_id = cur.fetchone()[0]
            print("Request id", last_id)

            if last_id is not None:
                print("Request id fetch from db")
                # Construct response
                 # Fetch status code , headers , body from response table with the request id fetched
                cur.execute("""
                            SELECT response_statuscode,response_headers,response_body from public.response 
                            WHERE request_id = %s;
                            """,
                            [last_id])
                response_code = cur.fetchone()[0]
                response_headers = cur.fetchone()[1]
                response_body = cur.fetchone()[2]
                print(response_code, response_headers, response_body)
                request.create_response(
                    status_code=response_code,
                    headers=response_headers,
                    body=response_body
                )

            else:
                print("Request doesnt exist")
                # If flag is true : call insert into db else raise an error
                # throw new exception

            conn.commit()
            print("Records Inserted successfully")
            conn.close()

        except Exception as exp:
            print("Got exception %s", (exp))
            conn.rollback()
            print("Request not found in database")
            # Call insert request
            conn.close()
        return;


    @staticmethod
    def create_table():
        print ("Init create table")
        conn = psycopg2.connect(database="project", user="postgres", password="postgres", host="127.0.0.1", port="5432")
        try:
            print("Connection created successfully")
            cur = conn.cursor()
            #body = request.body.decode('utf-8')
            #data = json.loads(body)

            cur.execute('''CREATE TABLE public.request
            (id SERIAL  PRIMARY KEY NOT NULL,
            request_url TEXT    NOT NULL,
            request_method  TEXT    NOT NULL,
            request_path    TEXT    NOT NULL,
            request_queryString TEXT    NOT NULL,
            request_params  TEXT,
            request_headers TEXT    NOT NULL,
            request_body TEXT,
            response_reason TEXT,
            response_status INT
            );''')

            print("Request Table Created ")

            cur.execute('''CREATE TABLE public.response
            (id SERIAL PRIMARY KEY NOT NULL,
            request_id INT REFERENCES request (id),
            response_body TEXT,
            response_statusCode  INT    NOT NULL,
            response_reason    TEXT,
            response_headers  TEXT
            );''')
            print("Response Table Created ")
            conn.commit()
            conn.close()
        except Exception as exp:
            print("Got exception " + exp)
            print("change not committed , fix the code and run again")
            conn.close()

    @staticmethod
    def unset_interceptor(driver):
        del driver.request_interceptor
        del driver.response_interceptor