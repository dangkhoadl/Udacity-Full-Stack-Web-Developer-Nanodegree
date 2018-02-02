#!/usr/bin/env python3
import psycopg2


DBNAME = "news"


def getQuery(query):
    conn = psycopg2.connect(database=DBNAME)
    cur = conn.cursor()
    cur.execute(query)
    results = cur.fetchall()
    conn.close()
    return results


if __name__ == '__main__':

    query1 = '''
        select articles.title, count(*) as views
        from articles, log
        where log.path like concat('%',articles.slug)
        group by articles.title
        order by views desc
        limit 3
        '''
    queryResult1 = getQuery(query1)

    query2 = '''
        select authors.name, count(*) as views
        from articles, authors, log
        where log.path like concat('%',articles.slug)
            and authors.id = articles.author
        group by authors.name
        order by views desc
        '''
    queryResult2 = getQuery(query2)

    query3 = '''
        select date(time), round(100.0
            * sum(
                case status
                    when '200 OK'then 0
                    else 1 end
            )
            / count(status),1)
        from log
        group by date(time)
        having round(100.0
            * sum(
                case status
                when '200 OK' then 0
                else 1 end
            )
            / count(status),1) > 1.0
        '''
    queryResult3 = getQuery(query3)

    # Open output file
    fileOut = open('output.out', 'w')

    # Display What are the most popular three articles of all time?
    fileOut.write(
        "1. What are the most popular three articles of all time ?\n")
    for result in queryResult1:
        fileOut.write(
            "\t%s - %s views\n" % (str(result[0]), str(result[1])))

    # Display What are the most popular three articles of all time?
    fileOut.write(
        "2. Who are the most popular article authors of all time ?\n")
    for result in queryResult2:
        fileOut.write(
            "\t%s - %s views\n" % (str(result[0]), str(result[1])))

    # Display On which days did more than 1% of requests lead to errors?
    fileOut.write(
        "3. On which days did more than 1% of requests lead to errors ?\n")
    for result in queryResult3:
        fileOut.write(
            "\t%s - %s" % (str(result[0]), str(result[1])) + '%' + " errors\n")

    # Close Output file
    fileOut.close()
