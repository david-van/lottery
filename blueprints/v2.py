from flask import Blueprint, jsonify, request
import pymysql
from datetime import date, datetime

bp = Blueprint('v2', __name__, url_prefix='/api/v2')

# @bp.route("getBetableMatches", methods=["GET"])
# def get_all_matches():
#     # 数据库连接配置
#     connection = pymysql.connect(
#         host="localhost",  # 数据库地址
#         user="root",  # 用户名
#         password="123456",  # 密码
#         database="lottery",  # 数据库名称
#         charset="utf8mb4",  # 字符集
#     )
#     # 获取当前日期（格式：YYYY-MM-DD）
#     today = date.today().strftime("%Y-%m-%d")
#     # 执行查询：查找当天的比赛
#     cursor = connection.cursor(pymysql.cursors.DictCursor)  # 使用字典游标获取字段名作为键
#     query = """
#         SELECT t1.*, t2.h, t2.a, t2.d,
#         t3.h AS rh, t3.a AS ra, t3.d AS rd,
#         t4.aa, t4.ad, t4.ah, t4.da, t4.dd, t4.dh, t4.ha, t4.hd, t4.hh,
#         t5.s0, t5.s1, t5.s2, t5.s3, t5.s4, t5.s5, t5.s6, t5.s7,
#         t6.s01s00, t6.s02s00, t6.s02s01, t6.s03s00, t6.s03s01, t6.s03s02, t6.s04s00, t6.s04s01, t6.s04s02,
#         t6.s05s00, t6.s05s01, t6.s05s02, t6.s_1sh,
#         t6.s00s00, t6.s01s01, t6.s02s02, t6.s03s03, t6.s_1sd,
#         t6.s00s01, t6.s00s02, t6.s01s02, t6.s00s03, t6.s01s03, t6.s02s03, t6.s00s04, t6.s01s04, t6.s02s04,
#         t6.s00s05, t6.s01s05, t6.s02s05, t6.s_1sa
#         FROM match_result t1
#         JOIN match_had t2 ON t1.match_id = t2.match_id
#         JOIN match_hhad t3 ON t1.match_id = t3.match_id
#         JOIN match_hafu t4 ON t1.match_id = t4.match_id
#         JOIN match_ttg t5 ON t1.match_id = t5.match_id
#         JOIN match_crs t6 ON t1.match_id = t6.match_id
#         WHERE date >= %s
#         ORDER BY t1.date ASC;
#     """
#     # cursor.execute(query, ("2024-11-23"))
#     cursor.execute(query, (today))
#     matches = cursor.fetchall()  # 获取所有匹配数据
#     # print(type(matches), type(matches[0]))
#     # 关闭数据库连接
#     cursor.close()
#     connection.close()

#     # 如果没有找到数据，返回一个空列表
#     if not matches:
#         # return jsonify({"message": "No matches found for today."}), 404
#         return jsonify({"data":{}, "msg":"未查询到今日比赛", "code":200})

#     match_list = []
#     for match in matches:
#         match["date"] = match["date"].strftime("%Y-%m-%d")
#         # 先添加基本信息
#         tmp = {"date": match["date"], "team_home": match["team_home"], "team_away": match["team_away"], "match_id": match["match_id"]}
#         # 添加非让球胜平负信息
#         had = {}
#         had['h'] = match["h"]
#         had['a'] = match['a']
#         had['d'] = match['d']
#         tmp['had'] = had
        
#         # 添加让球胜平负信息
#         hhad = {}
#         hhad['rh'] = match["rh"]
#         hhad['ra'] = match['ra']
#         hhad['rd'] = match['rd']
#         tmp['hhad'] = hhad

#         # 添加比分信息
#         crs = {}
#         crs['s01s00'], crs['s02s00'], crs['s02s01'], crs['s03s00'], crs['s03s01'], crs['s03s02'], crs['s04s00'], crs['s04s01'], crs['s04s02'], crs['s05s00'], crs['s05s01'], crs['s05s02'], crs['s_1sh'] = \
#         match['s01s00'], match['s02s00'], match['s02s01'], match['s03s00'], match['s03s01'], match['s03s02'], match['s04s00'], match['s04s01'], match['s04s02'], match['s05s00'], match['s05s01'], match['s05s02'], match['s_1sh']
#         crs['s00s00'], crs['s01s01'], crs['s02s02'], crs['s03s03'], crs['s_1sd'] = match['s00s00'], match['s01s01'], match['s02s02'], match['s03s03'], match['s_1sd']
#         crs['s00s01'], crs['s00s02'], crs['s01s02'], crs['s00s03'], crs['s01s03'], crs['s02s03'], crs['s00s04'], crs['s01s04'], crs['s02s04'], crs['s00s05'], crs['s01s05'], crs['s02s05'], crs['s_1sa'] = \
#         match['s00s01'], match['s00s02'], match['s01s02'], match['s00s03'], match['s01s03'], match['s02s03'], match['s00s04'], match['s01s04'], match['s02s04'], match['s00s05'], match['s01s05'], match['s02s05'], match['s_1sa']
#         tmp['crs'] = crs

#         # 添加半场胜平负信息
#         hafu = {}
#         for x in ('h', 'a', 'd'):
#             for y in ('h', 'a', 'd'):
#                 hafu[f'{x}{y}'] = match[f'{x}{y}']
#         tmp['hafu'] = hafu

#         # 添加总进球信息
#         ttg = {}
#         ttg['s0'], ttg['s1'], ttg['s2'], ttg['s3'], ttg['s4'], ttg['s5'], ttg['s6'], ttg['s7'] = match['s0'], match['s1'], match['s2'], match['s3'], match['s4'], match['s5'], match['s6'], match['s7']
#         tmp['ttg'] = ttg

#         match_list.append(tmp)
    
#     # 返回比赛信息
#     # return jsonify({"matches": msg})
#     return jsonify({"data":{"matches": match_list}, "msg":"查询成功", "code":200})


@bp.route("getBetableMatches", methods=["GET"])
def get_betable_matches():
    # 数据库连接配置
    connection = pymysql.connect(
        host="localhost",  # 数据库地址
        user="huan",  # 用户名
        password="huan",  # 密码
        database="lottery",  # 数据库名称
        charset="utf8mb4",  # 字符集
    )
    # 获取当前日期（格式：YYYY-MM-DD）
    today = date.today().strftime("%Y-%m-%d")
    # 执行查询：查找当天的比赛
    cursor = connection.cursor(pymysql.cursors.DictCursor)  # 使用字典游标获取字段名作为键
    query = """
        SELECT t1.*, t2.h, t2.a, t2.d
        FROM match_result t1
        JOIN match_had t2 ON t1.match_id = t2.match_id
        WHERE date >= %s
        ORDER BY t1.date ASC;
    """
    # cursor.execute(query, ("2024-11-23"))
    cursor.execute(query, (today))
    matches = cursor.fetchall()  # 获取所有匹配数据
    # print(type(matches), type(matches[0]))
    # 关闭数据库连接
    cursor.close()
    connection.close()

    # 如果没有找到数据，返回一个空列表
    if not matches:
        # return jsonify({"message": "No matches found for today."}), 404
        return jsonify({"data":{}, "msg":"未查询到今日比赛", "code":200})

    match_list = []
    for match in matches:
        match["date"] = match["date"].strftime("%Y-%m-%d")
        # 先添加基本信息
        tmp = { "matchId": match["match_id"], "date": match["date"], "teamHome": match["team_home"], "teamAway": match["team_away"]}
        # 添加非让球胜平负信息
        tmp['h'] = match["h"]
        tmp['a'] = match['a']
        tmp['d'] = match['d']

        match_list.append(tmp)
    
    # 返回比赛信息
    # return jsonify({"matches": msg})
    return jsonify({"data":{"matches": match_list}, "msg":"查询成功", "code":200})


@bp.route("getDetails", methods=["GET"])
def get_details():
    # 数据库连接配置
    connection = pymysql.connect(
        host="localhost",  # 数据库地址
        user="huan",  # 用户名
        password="huan",  # 密码
        database="lottery",  # 数据库名称
        charset="utf8mb4",  # 字符集
    )
    # 获取要查询的比赛id
    match_id = request.args.get("matchId")
    if match_id is None:
        return jsonify({"data":{"matches": None}, "msg":"未提供比赛Id", "code":400})
    # 执行查询
    cursor = connection.cursor(pymysql.cursors.DictCursor)  # 使用字典游标获取字段名作为键
    query = """
        SELECT t1.*, t2.h, t2.a, t2.d,
        t3.h AS rh, t3.a AS ra, t3.d AS rd,
        t4.aa, t4.ad, t4.ah, t4.da, t4.dd, t4.dh, t4.ha, t4.hd, t4.hh,
        t5.s0, t5.s1, t5.s2, t5.s3, t5.s4, t5.s5, t5.s6, t5.s7,
        t6.s01s00, t6.s02s00, t6.s02s01, t6.s03s00, t6.s03s01, t6.s03s02, t6.s04s00, t6.s04s01, t6.s04s02,
        t6.s05s00, t6.s05s01, t6.s05s02, t6.s_1sh,
        t6.s00s00, t6.s01s01, t6.s02s02, t6.s03s03, t6.s_1sd,
        t6.s00s01, t6.s00s02, t6.s01s02, t6.s00s03, t6.s01s03, t6.s02s03, t6.s00s04, t6.s01s04, t6.s02s04,
        t6.s00s05, t6.s01s05, t6.s02s05, t6.s_1sa
        FROM match_result t1
        JOIN match_had t2 ON t1.match_id = t2.match_id
        JOIN match_hhad t3 ON t1.match_id = t3.match_id
        JOIN match_hafu t4 ON t1.match_id = t4.match_id
        JOIN match_ttg t5 ON t1.match_id = t5.match_id
        JOIN match_crs t6 ON t1.match_id = t6.match_id
        WHERE t1.match_id = %s;
    """

    cursor.execute(query, (match_id))
    match = cursor.fetchone()  # 获取所有匹配数据
    # print(type(matches), type(matches[0]))
    # 关闭数据库连接
    cursor.close()
    connection.close()
    
    # 如果没有找到数据，返回一个空列表
    if not match:
        # return jsonify({"message": "No matches found for today."}), 404
        return jsonify({"data":{}, "msg":"未查询到比赛信息", "code":200})

    match["date"] = match["date"].strftime("%Y-%m-%d")
    data = {"date": match["date"], "team_home": match["team_home"], "team_away": match["team_away"], "match_id": match["match_id"]}

    # 添加非让球胜平负信息
    had = {}
    had['h'] = match["h"]
    had['a'] = match['a']
    had['d'] = match['d']
    data['had'] = had

    # 添加让球胜平负信息
    hhad = {}
    hhad['rh'] = match["rh"]
    hhad['ra'] = match['ra']
    hhad['rd'] = match['rd']
    data['hhad'] = hhad

    # 添加比分信息
    crs = {}
    crs['s01s00'], crs['s02s00'], crs['s02s01'], crs['s03s00'], crs['s03s01'], crs['s03s02'], crs['s04s00'], crs['s04s01'], crs['s04s02'], crs['s05s00'], crs['s05s01'], crs['s05s02'], crs['other_h'] = \
    match['s01s00'], match['s02s00'], match['s02s01'], match['s03s00'], match['s03s01'], match['s03s02'], match['s04s00'], match['s04s01'], match['s04s02'], match['s05s00'], match['s05s01'], match['s05s02'], match['s_1sh']
    crs['s00s00'], crs['s01s01'], crs['s02s02'], crs['s03s03'], crs['other_d'] = match['s00s00'], match['s01s01'], match['s02s02'], match['s03s03'], match['s_1sd']
    crs['s00s01'], crs['s00s02'], crs['s01s02'], crs['s00s03'], crs['s01s03'], crs['s02s03'], crs['s00s04'], crs['s01s04'], crs['s02s04'], crs['s00s05'], crs['s01s05'], crs['s02s05'], crs['other_a'] = \
    match['s00s01'], match['s00s02'], match['s01s02'], match['s00s03'], match['s01s03'], match['s02s03'], match['s00s04'], match['s01s04'], match['s02s04'], match['s00s05'], match['s01s05'], match['s02s05'], match['s_1sa']
    data['crs'] = crs

    # 添加半场胜平负信息
    hafu = {}
    for x in ('h', 'a', 'd'):
        for y in ('h', 'a', 'd'):
            hafu[f'{x}{y}'] = match[f'{x}{y}']
    data['hafu'] = hafu

    # 添加总进球信息
    ttg = {}
    ttg['s0'], ttg['s1'], ttg['s2'], ttg['s3'], ttg['s4'], ttg['s5'], ttg['s6'], ttg['s7'] = match['s0'], match['s1'], match['s2'], match['s3'], match['s4'], match['s5'], match['s6'], match['s7']
    data['ttg'] = ttg
    
    # 返回比赛信息
    return jsonify({"data":{"matches": data}, "msg":"查询成功", "code":200})

