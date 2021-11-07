# coding=utf-8
from __future__ import division

import os
import datetime
import random
import pytils.dt
from uuid import uuid4
from django.db import models
from django.utils.timezone import utc
from django.core.exceptions import ObjectDoesNotExist


def get_image_filename(instance, filename):
    """
        Для размещения файлов в директориях со случайным именем
    """
    uid = uuid4()
    return os.path.join(u'images', unicode(uid)) + ".jpg"


class Round(models.Model):
    """
        Хранилище информации о раундах. Просто и без всякой экзотики
    """
    FUTURE = '1'
    NOW = '2'
    PAST = '3'
    CORRUPTED = '4'

    ROUND_STATUS_CHOICES = (
        (FUTURE, u'Еще на начался'),
        (NOW, u'Текущий'),
        (PAST, u'Закончился'),
        (CORRUPTED, u'Коррумпирован блеать'),
    )

    number = models.IntegerField(verbose_name=u'Номер раунда', unique=True)
    status = models.CharField(verbose_name=u'Статус раунда', choices=ROUND_STATUS_CHOICES, max_length=18,
                              editable=False)
    begin_time = models.DateTimeField(verbose_name=u'Начало раунда', auto_now_add=True)
    end_time = models.DateTimeField(verbose_name=u'Конец раунда', default=None)

    #ВРЕМЯ ГОВНОКОДИТЬ!!!
    #Именно тут начинается леденящий душу пиздец.
    @staticmethod
    def get_next_round_time(now_time, delta_min=2, delta_max=10):
        delta = datetime.timedelta(minutes=random.choice(range(delta_min, delta_max, 1)))
        return now_time + delta

    @staticmethod
    def add_new_round():
        now_time = datetime.datetime.utcnow().replace(tzinfo=utc)
        try:
            last_round = Round.objects.last()
            last_round.status = Round.PAST
            last_round.end_time = now_time
            last_round.save()
            number = last_round.number
        except:
            print 'No Rounds Exist (warning)'
            number = 0

        one_round = Round.objects.create(number=number + 1, status=Round.NOW,
                                         end_time=Round.get_next_round_time(now_time))

        print 'Success adding new ROUND %s' % one_round.number
        return one_round

    @staticmethod
    def get_now_round():
        try:
            result = Round.objects.filter(status=Round.NOW)
            return result.last()

        except ObjectDoesNotExist:
            print 'Can not get now round'
            return None

        #Пара строк говнокода на случай всяческой хуйни
        except:
            print 'Can not get ROUND info'
            return None


    @staticmethod
    def get_now_round_number():
        try:
            now_round = Round.get_now_round()
            return now_round.number
        except:
            return None

    class Meta:
        verbose_name_plural = u"Раунды"
        verbose_name = u"Раунд"
        db_table = u'Round'

    def __unicode__(self):
        return u'Раунд %s' % self.number


class Team(models.Model):
    """
        Информация о командах
    """
    login = models.CharField(verbose_name=u'Логин', max_length=18, unique=True)
    name = models.CharField(verbose_name=u'Название команды', max_length=50, unique=True)
    image = models.ImageField(verbose_name=u'Лого', upload_to=get_image_filename, blank=True)
    network_address = models.CharField(verbose_name=u'Адрес/Подсеть', max_length=18, default='127.0.0.1/24')
    description = models.TextField(verbose_name=u'Описание', blank=True)
    server_ip = models.CharField(verbose_name=u'Адрес сервера', max_length=18, default='127.0.1.1')

    @property
    def services_score_now(self):
        return Team.get_team_sum_services_score(self)

    @property
    def advisory_score_now(self):
        return Team.get_team_sum_advisory_score(self)

    @property
    def services_rating_now(self):
        return Team.get_team_sum_services_rating(self)

    @property
    def advisory_rating_now(self):
        return Team.get_team_sum_advisory_rating(self)

    @property
    def sum_rating_now(self):
        return Team.get_team_rating(self)

    @staticmethod
    def get_team_by_id(team_id):
        try:
            return Team.objects.get(id=team_id)
        except:
            return None

    @staticmethod
    def get_team_service_score(team, service, one_round=Round.get_now_round()):
        try:
            return Score.get_team_service_points(team, service, one_round)
        except:
            return 0

    @staticmethod
    def get_team_sum_services_score(team, one_round=Round.get_now_round()):
        try:
            return Score.get_team_sum_points(team, one_round)
        except:
            return 0

    @staticmethod
    def get_team_sum_advisory_score(team):
        try:
            return Advisory.get_team_sum_advisory_points(team)
        except:
            return 0

    @staticmethod
    def get_team_sum_services_rating(team, one_round=Round.get_now_round()):
        max_score = 0
        try:
            for t in Team.objects.all():
                iter_score = Team.get_team_sum_services_score(t, one_round)
                if iter_score > max_score:
                    max_score = iter_score
        except:
            pass
        if max_score == 0:
            return 0
        else:
            team_score = Team.get_team_sum_services_score(team, one_round)
            if team_score <= 0:
                return 0
            else:
                return round(100 * team_score / max_score, 2)

    @staticmethod
    def get_team_sum_advisory_rating(team):
        max_score = 0
        try:
            for t in Team.objects.all():
                iter_score = Team.get_team_sum_advisory_score(t)
                if iter_score > max_score:
                    max_score = iter_score
        except:
            pass
        if max_score == 0:
            return 0
        else:
            return round(100 * Team.get_team_sum_advisory_score(team) / max_score, 2)

    @staticmethod
    def get_team_rating(team, one_round=Round.get_now_round()):
        max_rating = 0
        try:
            for t in Team.objects.all():
                iter_rating = Team.get_team_sum_services_rating(t, one_round) + Team.get_team_sum_advisory_rating(t)
                if iter_rating > max_rating:
                    max_rating = iter_rating
        except:
            pass
        if max_rating == 0:
            return 0
        else:
            return round(100 * (
                Team.get_team_sum_services_rating(team, one_round) + Team.get_team_sum_advisory_rating(
                    team)) / max_rating, 2)

    class Meta:
        verbose_name_plural = u"Команды"
        verbose_name = u"Команда"
        db_table = u'Team'

    def __unicode__(self):
        return u'{0:s} ({1:s})'.format(self.name, self.login)


class Service(models.Model):
    """
        Информация о сервисах
        Тупо какие у нас есть
    """
    number = models.CharField(verbose_name=u'Номер сервиса', max_length=10)
    name = models.CharField(verbose_name=u'Название сервиса', max_length=50)
    description = models.TextField(verbose_name=u'Описание', blank=True)
    network_address = models.IPAddressField(verbose_name=u'Адрес чекера', max_length=18, default='127.0.0.1')
    network_port = models.IntegerField(verbose_name=u'Порт чекера', default=80)

    class Meta:
        verbose_name_plural = u"Сервисы"
        verbose_name = u"Сервис"
        db_table = u'Service'

    def __unicode__(self):
        return u'{0:s} ({1:s})'.format(self.name, self.number)


class Flag(models.Model):
    """
        Флаги за раунд для конкретного сервиса конкретной команды
        Поля не редактируются, чтобы админы не обмудились
    """
    round = models.ForeignKey(Round, verbose_name=u'Раунд', editable=False)
    service = models.ForeignKey(Service, verbose_name=u'Сервис', editable=False)
    team = models.ForeignKey(Team, verbose_name=u'Команда', editable=False)
    flag = models.CharField(max_length=33, verbose_name=u'Флаг', editable=False)

    @staticmethod
    def get_new_flag():
        return os.urandom(16).encode('hex') + "="

    @property
    def is_actual_now(self):
        """
            Воспользуемся при проверке отправленных флагов
            Вдруг они протухли
        """
        return self.round.status == Round.NOW

    @staticmethod
    def add_flags(one_round):
        try:
            for one_team in Team.objects.all():
                for one_service in Service.objects.all():
                    try:
                        Flag.objects.create(round=one_round, service=one_service, team=one_team, flag=Flag.get_new_flag())
                    except:
                        print "Some shit with flags creating!"
                        return False
            return True
        except Team.DoesNotExist:
            print 'Not teams in database'
            return False
        except Service.DoesNotExist:
            print 'Not services in database'
            return False
        except:
            print 'Can not add flags'
            return False

    class Meta:
        verbose_name_plural = u"Флаги"
        verbose_name = u"Флаг"
        db_table = u'RoundFlag'


class Advisory(models.Model):
    team = models.ForeignKey(Team, verbose_name=u'Команда')
    service = models.ForeignKey(Service, verbose_name=u'Сервис')
    points = models.IntegerField(verbose_name=u'Очки', default=0)
    vuln_text = models.TextField(verbose_name=u'Описание уязвимости', null=True, blank=True, default="Отсутствует")
    exploit_text = models.TextField(verbose_name=u'Описание эксплойта', null=True, blank=True, default="Отсутствует")
    defence_text = models.TextField(verbose_name=u'Описание способов защиты', null=True, blank=True,
                                    default="Отсутствует")
    datetime = models.DateTimeField(verbose_name=u'Время', auto_now_add=True, editable=False)
    is_visible = models.BooleanField(verbose_name=u'Виден участникам', default=False)

    @staticmethod
    def get_team_service_advisory_points(one_team, one_service):
        team_advisories = Advisory.objects.filter(team=one_team, service=one_service)
        service_advisory_points = 0
        for advisory in team_advisories:
            service_advisory_points += advisory.points
        return service_advisory_points

    @staticmethod
    def get_team_sum_advisory_points(one_team):
        team_advisories = Advisory.objects.filter(team=one_team)
        advisory_points = 0
        for advisory in team_advisories:
            advisory_points += advisory.points
        return advisory_points

    @staticmethod
    def get_team_advisories(one_team):
        return Advisory.objects.filter(team=one_team)

    class Meta:
        verbose_name_plural = u"Адвайзори"
        verbose_name = u"Адвайзори"
        db_table = u'Advisory'

    def __unicode__(self):
        return u'Адвайзори команды %s' % self.team


class Score(models.Model):
    """
        Я предполагаю создавать Score в каждом раунде
        для каждого сервиса каждой команды
        и потом на основе этой херни считать очки и смотреть историю набирания очков
	"""

    UNDEFINED = '0'
    UP = '1'
    DOWN = '2'
    MUMBLE = '3'
    CORRUPTED = '4'

    SERVICE_STATUS_CHOICES = (
        (UNDEFINED, u'???'),
        (UP, u'ОК'),
        (DOWN, u'DOWN'),
        (MUMBLE, u'MUMBLE'),
        (CORRUPTED, u'CORRUPTED'),
    )

    round = models.ForeignKey(Round, verbose_name=u'Раунд')
    team = models.ForeignKey(Team, verbose_name=u'Команда')
    service = models.ForeignKey(Service, verbose_name=u'Сервис')
    status = models.CharField(verbose_name=u'Статус', choices=SERVICE_STATUS_CHOICES, max_length=18, default=UNDEFINED)
    service_points = models.IntegerField(verbose_name=u'Очки', default=0)
    comment = models.CharField(verbose_name=u'Комментарий', blank=True, default="default", max_length=32)


    @staticmethod
    def get_team_service_points(one_team, one_service, one_round=Round.get_now_round()):
        try:
            result = 0
            for score in Score.objects.filter(team=one_team, service=one_service, round__lte=one_round):
                result += score.service_points
            return result
        except:
            return None


    @staticmethod
    def get_team_service_status(one_team, one_service, one_round=Round.get_now_round()):
        try:
            result = Score.objects.filter(team=one_team, service=one_service, round=one_round).last()
            return result.status
        except:
            return None


    @staticmethod
    def get_team_service_status_display(one_team, one_service, one_round=Round.get_now_round()):
        try:
            result = Score.objects.filter(team=one_team, service=one_service, round=one_round).last()
            return result.get_status_display()
        except:
            return None


    @staticmethod
    def get_team_sum_points(one_team, one_round=Round.get_now_round()):
        try:
            sum_points = 0
            for score in Score.objects.filter(team=one_team, round__lte=one_round):
                sum_points += score.service_points
            return sum_points
        except:
            return None


    @staticmethod
    def add_scores(one_round=Round.get_now_round()):
        try:
            for one_team in Team.objects.all():
                for one_service in Service.objects.all():
                    Score.objects.create(round=one_round, team=one_team, service=one_service, status=Score.UNDEFINED,
                                         service_points=0, comment="new round auto beginning")
        except:
            print "Can not add scores for %s round" % one_round.number


    class Meta:
        verbose_name_plural = u"Счет"
        verbose_name = u"Счет"
        db_table = u'Score'


class Log(models.Model):
    INCORRECT = '1'
    UNCHECKED = '2'
    CHECKED = '3'

    LOG_STATUS_CHOICES = (
        (INCORRECT, u'INCORRECT'),
        (UNCHECKED, u'UNCHECKED'),
        (CHECKED, u'CHECKED'),
    )

    team = models.ForeignKey(Team, verbose_name=u'Команда')
    flag = models.CharField(max_length=33, verbose_name=u'Флаг', default=None, editable=False)
    round = models.ForeignKey(Round, verbose_name=u'Раунд')
    datetime = models.DateTimeField(verbose_name=u'Время', auto_now_add=True, editable=False)
    status = models.CharField(max_length=10, verbose_name=u'Статус', choices=LOG_STATUS_CHOICES, default=UNCHECKED,
                              editable=False)

    class Meta:
        verbose_name_plural = u"Отправленные флаги"
        verbose_name = u"Отправленный флаг"
        db_table = u'Flag_Log'


class MainParams(models.Model):
    IS_BEGIN = u"Соревнования начались"
    IS_ENDED = u"Соревнования окончены"
    name = models.CharField(u'Название', max_length=20, default=u'Основные параметры системы', editable=False)
    start_time = models.DateTimeField(u'Начало соревнований', default=datetime.datetime.utcnow().replace(tzinfo=utc))
    end_time = models.DateTimeField(u'Конец соревнований',
                                    default=datetime.datetime.utcnow().replace(tzinfo=utc) + datetime.timedelta(
                                        hours=10))
    started = models.BooleanField(verbose_name=IS_BEGIN, default=False)
    ended = models.BooleanField(verbose_name=IS_ENDED, default=False)

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super(MainParams, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()

    @staticmethod
    def check_start_time():
        try:
            params = MainParams.objects.get(id=1)
        except:
            return None

        if not params.started:
            now = datetime.datetime.utcnow().replace(tzinfo=utc)
            start_time = params.start_time
            if start_time < now:
                params.started = True
                params.save()
                return None
            else:
                return pytils.dt.distance_of_time_in_words(from_time=start_time, to_time=now, accuracy=3)
        else:
            return None

    @staticmethod
    def check_afterparty_time():
        try:
            params = MainParams.objects.get(id=1)
        except:
            return None

        if not params.ended:
            end_time = params.end_time
            now = datetime.datetime.utcnow().replace(tzinfo=utc)
            if end_time < now:
                params.ended = True
                params.save()
                return None
            else:
                return pytils.dt.distance_of_time_in_words(from_time=end_time, to_time=now, accuracy=3)

        else:
            return None

    class Meta:
        verbose_name_plural = u"Основные параметры"
        verbose_name = u"Основные параметры"
        db_table = u'MainParams'


class News(models.Model):
    caption = models.CharField(max_length=30, verbose_name=u'Название новости', default=u'CTRL-PNZ', blank=True)
    author = models.CharField(max_length=30, verbose_name=u'Автор новости', default=u'CTRL-PNZ', blank=True)
    text = models.TextField(verbose_name=u'Текст новости')
    datetime = models.DateTimeField(verbose_name=u"Время размещения", auto_now_add=True, editable=False)

    class Meta:
        verbose_name_plural = u"Новости от разработчиков"
        verbose_name = u"Новость"
        db_table = u'News'

    def __unicode__(self):
        return u'%s' % self.caption


class Comment(models.Model):
    caption = models.CharField(max_length=30, verbose_name=u'Название комментария', default=u'Без названия', blank=True)
    nickname = models.CharField(max_length=30, verbose_name=u'Никнейм', default=u'Аноним', blank=True)
    team = models.ForeignKey(Team, verbose_name=u'Команда')
    new = models.ForeignKey(News, verbose_name=u'Новость')
    text = models.TextField(verbose_name=u'Текст комментария')
    datetime = models.DateTimeField(verbose_name=u"Время размещения", auto_now_add=True, editable=False)

    class Meta:
        verbose_name_plural = u"Комментарии"
        verbose_name = u"Комментарий"
        db_table = u'Comments'

    def __unicode__(self):
        return u'%s' % self.caption