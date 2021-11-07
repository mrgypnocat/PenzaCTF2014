# coding=utf-8
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.template import RequestContext, Context, loader
from django.core.context_processors import csrf
from django.conf import settings
from django.utils import timezone
from Adjudicator.models import *
from Adjudicator.utils import *


#Декоратор для показа отдельных вьюх только во время игры
def game_time_control(f):
    def wrapped_f(request, *args, **kw):
        try:
            params = MainParams.objects.get(id=1)
        except:
            raise Http404

        if not params.started or params.ended:
            raise Http404

        return f(request, *args, **kw)

    return wrapped_f


# Одна новость со всеми комментариями и формой добавления новых
@csrf_exempt
def one_new_view(request, new_id):
    one_team = get_team_by_request(request) or None
    one_new = get_object_or_404(News, id=new_id)

    if request.method == 'POST':
        comment_nickname = request.POST.get('nickname') or None
        comment_text = request.POST.get('text') or u"НЛО прилетело и ничего не написало О_о"
        try:
            Comment.objects.create(nickname=comment_nickname, team=one_team, new=one_new, text=comment_text)
        except:
            print "Some shit with news creating"

    data = ({
                'author': one_new.author,
                'caption': one_new.caption,
                'datetime': one_new.datetime,
                'text': one_new.text,
                'comments': [{
                                 'caption': com.caption,
                                 'nickname': com.nickname,
                                 'image': com.team.image,
                                 'team': com.team.name,
                                 'datetime': com.datetime,
                                 'text': com.text,
                             } for com in Comment.objects.filter(new=one_new).order_by('datetime')]
            })

    return render_to_response('one_new_page.html',
                              {'data': data,
                               'author': one_team}, context_instance=RequestContext(request))


# Список всех новостей со всем говном и последних комментов к ним
def all_news_view(request):
    data = [{
                'author': one_new.author,
                'caption': one_new.caption,
                'datetime': one_new.datetime,
                'text': one_new.text,
                'new_id': one_new.id,
                'comments_num': Comment.objects.filter(new=one_new).count(),
                'last_comment': [{
                                     'caption': com.caption,
                                     'nickname': com.nickname,
                                     'image': com.team.image,
                                     'team': com.team.name,
                                     'datetime': com.datetime,
                                     'text': com.text,
                                 } for com in Comment.objects.filter(new=one_new).order_by('datetime').reverse()[:1]]
            } for one_new in News.objects.all()]

    return render_to_response('news_page.html',
                              {'data': data}, context_instance=RequestContext(request))


@csrf_exempt
def advisory_view(request):
    one_team = get_team_by_request(request) or None
    if request.method == 'POST':
        try:
            advisory_vuln_text = request.POST.get('vulntext') or None
            advisory_exploit_text = request.POST.get('exploittext') or None
            advisory_defence_text = request.POST.get('defencetext') or None
            advisory_service = Service.objects.get(id=request.POST.get('service_id'))
            Advisory.objects.create(team=one_team, service=advisory_service, vuln_text=advisory_vuln_text,
                                    exploit_text=advisory_exploit_text, defence_text=advisory_defence_text)
        except:
            print "some advisories shit"

    services_choice = [{
                           'service_name': s.name or None,
                           'service_id': s.id or None,
                       } for s in Service.objects.all()]

    data = [{
                'team': one_advisory.team.name or None,
                'image': one_advisory.team.image or None,
                'service': one_advisory.service.name or None,
                'points': one_advisory.points or "0",
                'vuln_text': one_advisory.vuln_text or None,
                'exploit_text': one_advisory.exploit_text or None,
                'defence_text': one_advisory.defence_text or None,
                'datetime': one_advisory.datetime or None,
            } for one_advisory in Advisory.objects.filter(is_visible=True).order_by('datetime')]

    return render_to_response('advisory_page.html',
                              {'data': data,
                               'author': one_team,
                               'services_choice': services_choice or None}, context_instance=RequestContext(request))


def scoreboard_view(request, one_round_number=None):
    #Небольшая затычка, из-за особенностей работы Django
    if one_round_number is None:
        one_round = Round.get_now_round()
        try:
            one_round_number = one_round.number
        except:
            one_round_number = 0
    else:
        try:
            one_round = Round.objects.get(number=one_round_number)
        except:
            raise Http404

    # Oh Shit!
    rounds = Round.objects.all() or None
    services = Service.objects.all() or None
    teams = Team.objects.all() or None

    try:
        last_new = News.objects.latest('datetime').datetime
    except:
        last_new = None

    try:
        last_advisory = Advisory.objects.filter(is_visible=True).latest('datetime').datetime
    except:
        last_advisory = None

    services_list = []
    for s in services:
        services_list.append(s.name)

    info = ({
                'news_date': last_new or None,
                'news_count': News.objects.count(),
                'advisory_date': last_advisory or None,
                'advisory_count': Advisory.objects.filter(is_visible=True).count(),
            })

    data = [{
                'team_name': t.name or None,
                'team_id': t.id or None,
                'team_image': t.image or None,
                'team_ip': t.server_ip or None,
                'summary_rating': Team.get_team_rating(t, one_round) or 0,
                'services_rating': Team.get_team_sum_services_rating(t, one_round) or 0,
                'advisory_rating': Team.get_team_sum_advisory_rating(t) or 0,
                'services_score': Team.get_team_sum_services_score(t, one_round) or 0,
                'advisory_score': Team.get_team_sum_advisory_score(t) or 0,
                'services': [{
                                 'verbose_status': Score.get_team_service_status_display(one_team=t, one_service=s,
                                                                                         one_round=one_round) or "???",
                                 'status': Score.get_team_service_status(one_team=t, one_service=s,
                                                                         one_round=one_round) or None,
                                 'points': Score.get_team_service_points(one_team=t, one_service=s,
                                                                         one_round=one_round) or 0,
                             } for s in services]
            } for t in teams]

    data.sort(key=lambda x: x['summary_rating'], reverse=True)

    for (i, d) in enumerate(data):
        d['place'] = i + 1

    try:
        navigation = ({
                          'first': rounds.first().number or None,

                          'prev': [{
                                       'number': r.number,
                                   } for r in rounds.filter(number__lt=one_round_number)[one_round.number - 4:]]
                          if one_round.number - 4 > 0
                          else rounds.filter(number__lt=one_round_number)
                          or None,

                          'now': ({
                                      'number': one_round.number or None,
                                      'begin': one_round.begin_time or None,
                                  }),

                          'next': [{
                                       'number': r.number
                                   } for r in rounds.filter(number__gt=one_round_number)[:3]] or None,

                          'last': rounds.last().number or None,
                      })
    except:
        navigation = ()

    return render_to_response('scoreboard_page.html',
                              {'services_list': services_list,
                               'data': data,
                               'navigation': navigation,
                               'info': info,
                               'timer': check_game_time()
                              }, context_instance=RequestContext(request))


@csrf_exempt
def check_flag_view(request):
    one_team = get_team_by_request(request) or None
    status = None
    get_form = False
    flag = None
    
    if one_team is not None:
        try:
            params = MainParams.objects.get(id=1)
            if params.started and not params.ended:
                get_form = True
        except:
            print "Not params added"    
    
        if request.method == 'POST':            
            one_round = Round.get_now_round()
            flag = request.POST.get('flag') or None

            try:
                log = Log.objects.filter(team=one_team, round=one_round)
                last_log = log.last()
                time = (timezone.now() - last_log.datetime).seconds
            except:
                time = 2
                pass

            if time > 1:
                try:
                    sended_flag = Flag.objects.get(flag=flag, round=one_round)
                    if sended_flag.team == one_team:
                        status = Log.INCORRECT
                        print u"Own flags from %s" % one_team.name
                    else:
                        status = Log.UNCHECKED

                except:
                    status = Log.INCORRECT
                    print u"Incorrect flag from %s" % one_team.name

                if log.filter(flag=flag):
                    status = Log.INCORRECT
                    print u"Multiple flag sending from %s" % one_team.name

                Log.objects.create(flag=flag, team=one_team, round=one_round, status=status)

            else:
                flag = "Don't brute us!"
                print u"Team %s is trying to bruteforse us!" % one_team.name

    return render_to_response('flag_check_page.html',
                              {'data': flag,
                               'get_form': get_form,
                               'timer': check_game_time() or None,
                              }, context_instance=RequestContext(request))


def main_view(request):
    template = loader.get_template("main_page.html")
    context = Context({
        'team': get_team_by_request(request) or None,
        'team_address': get_ip(request) or None,
    })
    context.update(csrf(request))
    return HttpResponse(template.render(context), mimetype="text/html")


def check_view(request):
	#some shitcode, I haven't some time to mindfuck
	do_something = False
	try:
		params = MainParams.objects.get(id=1)
		if params.started and not params.ended:
			do_something = True
	except:
		print "Not params added"    
			
	if do_something:
		one_round = Round.get_now_round()
		info = check_new_round_time(one_round)
		print info
	else:
		info = "Game over"
    return HttpResponse(info)


"""
def test_view(request):
    template = loader.get_template("test.html")

    go_to_new_round()

    data = [{
                'service': one_service.number,
                'teams':
                    [{
                         'team': one_team.login,
                         'network_address': one_team.network_address,
                         'flag': Flag.objects.filter(round=Round.get_now_round_number(), service=one_service,
                                                     team=one_team).last().flag or None,
                     } for one_team in Team.objects.all()]
            } for one_service in Service.objects.all()]
    json_data = json.dumps(data)
    super_data = json.loads(json_data)

    context = Context({
        'json': json_data,
        'super_data': super_data,
        'round': Round.get_now_round_number(),
    })
    return HttpResponse(template.render(context), mimetype="text/html")
"""