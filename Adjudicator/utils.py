# coding=utf-8
import datetime, pytils.dt
from ipaddr import IPAddress, IPNetwork
from django.utils.timezone import utc
import json
import socket
from Adjudicator.models import Team, MainParams, Round, Service, Flag, Score, Log


def address_in_network(ipaddr, network):
    user_ip = IPAddress(ipaddr)
    w_ip = IPNetwork(network)
    return user_ip in w_ip


def get_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_team_by_request(request):
    client_ip = get_ip(request)
    for t in Team.objects.all():
        if address_in_network(client_ip, t.network_address):
            return t
    return None


def check_game_time():
    try:
        params = MainParams.objects.get(id=1)
    except:
        return u"Параметры системы не заданы"

    if not params.ended:
        now_time = datetime.datetime.utcnow().replace(tzinfo=utc)
        start_time = params.start_time
        end_time = params.end_time

        if not params.started:
            if start_time < now_time:
                params.started = True
                params.save()

                return u"Соревнования окончатся " + pytils.dt.distance_of_time_in_words(from_time=end_time,
                                                                                        to_time=now_time, accuracy=3)
            else:
                return u"Соревнования начнутся " + pytils.dt.distance_of_time_in_words(from_time=start_time,
                                                                                       to_time=now_time, accuracy=3)
        else:
            if end_time < now_time:
                params.ended = True
                params.save()
                return u"Соревнования окончены!"
            else:
                return u"Соревнования окончатся " + pytils.dt.distance_of_time_in_words(from_time=end_time,
                                                                                        to_time=now_time, accuracy=3)
    else:
        return u"Соревнования окончены!"


def check_new_round_time(one_round=Round.get_now_round()):

    if one_round is None:
        go_to_new_round(one_round)
        return "It's time to adding first round!"

    else:
        now_time = datetime.datetime.utcnow().replace(tzinfo=utc)
        end_time = one_round.end_time

        if now_time > end_time:
            go_to_new_round(one_round)
            return "It's time to adding new round!"
        else:
            return "New rounds time isn't come..."


def go_to_new_round(old_round=Round.get_now_round()):
    #Конец текущего раунда

    #Если это не первый раунд
    #Подводим итоги раунда
    if old_round is not None:

        base_points = 100

        set_teams_services_statuses(one_round=old_round, set_points=base_points * Team.objects.count())

        log_objects = Log.objects.filter(round=old_round, status=Log.UNCHECKED)

        for one_log_object in log_objects:

            print u"calculating score for %s" % one_log_object.team.name

            flag_object = Flag.objects.filter(round=old_round, flag=one_log_object.flag).last() or None
            if flag_object is not None:
                attacker_team = one_log_object.team
                victim_team = flag_object.team
                vuln_service = flag_object.service

                #Getting attacker's service status
                attacker_score_object = Score.objects.filter(round=old_round, team=attacker_team, service=vuln_service).last()

                if attacker_score_object is not None:
                    if attacker_score_object.status == Score.UP:
                        #Attacker points
                        Score.objects.create(round=old_round,
                                             team=attacker_team,
                                             service=vuln_service,
                                             status=Score.UP,
                                             service_points=base_points,
                                             comment=u"points for attacking %s" % victim_team)

                        #Victim points
                        Score.objects.create(round=old_round,
                                             team=victim_team,
                                             service=vuln_service,
                                             status=Score.objects.filter(
                                                 round=old_round,
                                                 team=victim_team,
                                                 service=vuln_service
                                             ).last().status,
                                             service_points=-base_points,
                                             comment=u"points to attacker %s" % attacker_team)
                    else:
                        print u"Attacker's service %s is down" % attacker_score_object.service.name
                else:
                    print u"can not get attacker score object for %s" % attacker_team

            else:
                print u"Can not find flag object to %s flag" % one_log_object.flag

    else:
        print "First round, adding new round"

    #Добавляем новый раунд
    new_round = Round.add_new_round()
    Score.add_scores(new_round)

    #Добавляем и рассылаем флаги
    set_round_flags(new_round)

    #Все, можно играть =)


def set_teams_services_statuses(one_round, set_points=0):
    def parse_status(status):
        if status == "UP":
            return Score.UP
        if status == "MUMBLE":
            return Score.MUMBLE
        if status == "CORRUPTED":
            return Score.CORRUPTED
        if status == "DOWN":
            return Score.DOWN
        return Score.UNDEFINED

    for one_service in Service.objects.all():
        #парсинг Json
        print "Ping to %s" % one_service.network_address, one_service.network_port                        
            
        try:
            jsondata = send_get_data("ping", one_service.network_address, one_service.network_port)
            data = json.loads(jsondata)
        
        except: 
            print "Checker for %s send some shit" % one_service.name
            continue

        service_number = data['service'] or None
        round_number = data['round_number'] or None

        all_teams_service_dict = data['teams'] or None        
        if all_teams_service_dict is None:
             continue

        for one_object in all_teams_service_dict:
            team_login = one_object['team']
            network_address = one_object['network_address']
            status = one_object['status']

            one_team = Team.objects.filter(login=team_login).last()

            try:
                score_objects = Score.objects.filter(round=one_round,
                                                     team=one_team,
                                                     service=one_service,
                                                     comment="round auto ending"
                                                    )

                if score_objects.count() == 0:
                    Score.objects.create(round=one_round,
                                         team=one_team,
                                         service=one_service,
                                         status=parse_status(status),
                                         service_points=set_points if status == "UP" else 0,
                                         comment="round auto ending"
                                        )
                    print u"Success scores creating for %s" % team_login

                else:
                    print u"Service %s send some shit" % one_service.name
                    continue

            except:
                print u"Can not find score for team %s" % team_login
                continue


def set_round_flags(one_round):
    one_round_number = one_round.number
    if Flag.add_flags(one_round):
        for one_service in Service.objects.all():
            data = ({
                        'service': one_service.number,
                        'round_number': one_round_number,
                        'teams': [{
                                      'team': one_team.login,
                                      'network_address': one_team.server_ip,
                                      'flag': Flag.objects.filter(round=one_round_number, service=one_service,
                                                                  team=one_team).last().flag,
                                  } for one_team in Team.objects.all()]
                    })
            send_get_data(json.dumps(data), one_service.network_address, one_service.network_port)
    else:
        print "Flags not sended because can not add flags"


def send_get_data(data, recv_addr, recv_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect((recv_addr, int(recv_port)))
        s.send(data)
        result = s.recv(1024)
        s.close()
        return result or None
    except:
        print u"Something wrong with %s" % (str(recv_addr) + ":" + str(recv_port))
        return None