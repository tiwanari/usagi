import csv
import psycopg2
import MySQLdb

class PSQLHandle(object):
    SQL_GET_META_DATA = """
SELECT
    CASE WHEN schema_name = 'public' THEN table_name
        ELSE schema_name || '.' || table_name END AS title,
    schema_name || ' '
    || table_name || ' '
    || table_comment || ' '
    || string_agg(column_name || ' ' || column_comment, ' ') AS content
FROM
(
SELECT
  psut.relid table_oid,
    psut.schemaname schema_name,
    psut.relname table_name,
    CASE WHEN pd.description IS NULL THEN '' ELSE pd.description END table_comment
FROM
    pg_stat_user_tables psut
LEFT JOIN
(
    SELECT *
    FROM
        pg_description pd
    WHERE
        pd.objsubid IS NULL OR pd.objsubid = 0
) pd
ON
    psut.relid = pd.objoid
) r
JOIN
(
SELECT
  psut.relid table_oid,
    pa.attname column_name,
    CASE WHEN pd.description IS NULL THEN '' ELSE pd.description END column_comment
FROM
    pg_stat_user_tables psut
JOIN
    pg_attribute pa
ON
    psut.relid = pa.attrelid
LEFT JOIN
(
    SELECT *
    FROM
        pg_description pd
    WHERE
        pd.objsubid IS NULL OR pd.objsubid != 0
) pd
ON
    psut.relid = pd.objoid AND pd.objsubid = pa.attnum
) s
USING (table_oid)
GROUP BY schema_name, table_name, table_comment"""

    def __init__(self, name, dsn):
        self.name = name
        self.dsn = dsn

    def connect(self):
        self.connection = psycopg2.connect(self.dsn)

    def close(self):
        self.connection.close()

    def copy_raw_meta_data(self, output_path, append=False):
        cur = self.connection.cursor()
        f = open(output_path, 'a' if append else 'w')
        sql_copy = "COPY (%s) TO STDOUT WITH CSV" % PSQLHandle.SQL_GET_META_DATA
        cur.copy_expert(sql_copy, f)
        f.close()
        cur.close()


class MySQLHandle(object):
    SQL_GET_META_DATA = """
SELECT
    concat(t.table_schema, '.', t.table_name) AS title,
    concat_ws(' ', t.table_schema, t.table_name, t.table_comment,
        group_concat(
            concat(c.column_name, ' ', c.column_comment) SEPARATOR ' '
        )
    ) AS content
FROM
    information_schema.tables t,
    information_schema.columns c
WHERE
    t.table_schema NOT IN
    (
        'performance_schema',
        'mysql',
        'sys',
        'information_schema'
    )
AND t.table_name = c.table_name
AND t.table_schema IN {databases}
GROUP BY
    t.table_schema, t.table_name, t.table_comment"""

    def __init__(self, name, params):
        self.name = name
        self.databases = [d.strip() for d in params.pop('db').split(',')]
        self.params = params

    def connect(self):
        self.connection = MySQLdb.connect(**self.params)

    def close(self):
        self.connection.close()

    def copy_raw_meta_data(self, output_path, append=False):
        cur = self.connection.cursor()
        f = open(output_path, 'a' if append else 'w')
        cur.execute(MySQLHandle.SQL_GET_META_DATA.format(
            databases=str(tuple(self.databases))))
        writer = csv.writer(f, lineterminator='\n')
        writer.writerows(list(cur))
        f.close()
        cur.close()
