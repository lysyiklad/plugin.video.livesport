# -*- coding: utf-8 -*-

import bs4

hockey = u"""
<li class="supermain"><p>1-й период (2:2)</p></li>
<li class="match_review_left"><div><span class="number">01:58</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">Кудако В. (Задержка клюшкой)</span></div></li>
<li class="match_review_left"><div><span class="number">06:33</span><span class="icon hockey-ball">&nbsp;</span><span class="name">Кодола В. Хабаров М. + Петунин А. </span></div></li>
<li class="match_review_right"><div><span class="number">07:40</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">(Удар клюшкой) Погоришный О.</span></div></li>
<li class="match_review_left"><div><span class="number">09:16</span><span class="icon hockey-ball">&nbsp;</span><span class="name">Морозов Е. Яковлев Е. + Кудако В. </span></div></li>
<li class="match_review_left"><div><span class="number">09:56</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">Хохлов И. (Задержка клюшкой)</span></div></li>
<li class="match_review_right"><div><span class="number">11:17</span><span class="icon hockey-ball">&nbsp;</span><span class="name"> Эллис М. + Стремвалл М. Росен Р.</span></div></li>
<li class="match_review_right"><div><span class="number">15:06</span><span class="icon hockey-ball">&nbsp;</span><span class="name"> Лугин Д. + Коллинз Ш. Александров Ю.</span></div></li>
<li class="match_review_right"><div><span class="number">19:30</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">(Подножка) Архипов Д.</span></div></li>
<li class="supermain"><p>2-й период (1:0)</p></li>
<li class="match_review_right"><div><span class="number">01:21</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">(Задержка клюшкой) Макаренко П.</span></div></li>
<li class="match_review_left"><div><span class="number">08:23</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">Макеев Н. (Подножка)</span></div></li>
<li class="match_review_left"><div><span class="number">12:20</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">Якимов Б. (Подножка)</span></div></li>
<li class="match_review_right"><div><span class="number">17:37</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">(Подножка) Алтыбармакян А.</span></div></li>
<li class="match_review_left"><div><span class="number">17:52</span><span class="icon hockey-ball">&nbsp;</span><span class="name">Яковлев Е. Гераськин И. + Кудако В. </span></div></li>
"""

sli_hockey = """
<li class="match_review_left">
	<div>
		<span class="number">01:58</span>
		<span class="icon block-time" title="Штраф на кол-во минут: 2">2</span>
		<span class="name">Кудако В. (Задержка клюшкой)</span>	
	</div>	
</li>
"""

american_football = """
<li class="supermain"><p>1-я четверть (3:3)</p></li>
<li class="match_review_left"><div><span class="number">01:49</span><span class="name">Bailey D.</span></div></li>
<li class="match_review_right"><div><span class="number">13:00</span><span class="name">Crosby M.</span></div></li>
<li class="supermain"><p>2-я четверть (7:6)</p></li>
<li class="match_review_left"><div><span class="number">01:27</span><span class="name">Diggs S.</span></div></li>
<li class="match_review_left"><div><span class="number">01:27</span><span class="name">Bailey D.</span></div></li>
<li class="match_review_right"><div><span class="number">08:00</span><span class="name">Crosby M.</span></div></li>
<li class="match_review_right"><div><span class="number">14:59</span><span class="name">Crosby M.</span></div></li>
<li class="supermain"><p>3-я четверть (0:8)</p></li>
<li class="match_review_right"><div><span class="number">12:57</span><span class="name">Джонс А.</span></div></li>
<li class="match_review_right"><div><span class="number">12:57</span><span class="name">Allison G.</span></div></li>
<li class="supermain"><p>4-я четверть (0:6)</p></li>
<li class="match_review_right"><div><span class="number">09:09</span><span class="name">Джонс А.</span></div></li>
<li class="match_review_right"><div><span class="number">09:09</span><span class="name">Crosby M.</span></div></li>

"""

#print reviews.encode('utf-8')
home = u'ХК Нефтехимик'
guest = u'ХК Ак Барс'

print len(home)
# print len(home.encode('utf-8'))

print len(guest)
# print len(guest.encode('utf-8'))

OBREZ = 20


def format_str_column_width(txt, column_width):
    return u'{1:*<{0:}}|'.format(column_width, txt[:column_width] if len(txt) > column_width else txt)


print format_str_column_width(home, 20).encode('utf-8')
print format_str_column_width(guest, 20).encode('utf-8')


# links = []

# tag_reviews = bs4.BeautifulSoup(hockey, 'html.parser')

# lis = tag_reviews.findAll('li')

# for li in tag_reviews.findAll('li'):
#     class_ = li['class'][0]
#     #print class_
#     if class_ == u'supermain':
#         #print li.text
#         links.append(li.text)
#     else:
#         if class_ == 'match_review_left':            
#             link = u'{:<20}'.format(home)
#         else:
#             link = u'{:<20}'.format(guest)
#         div = li.find('div')
#         spans = div.findAll('span')
#         for s in spans:
#             txt = u''
#             #print s['class']
#             if len(s['class']) == 2:
#                 if s['class'][0] == u'icon':
#                     if s['class'][1] == u'block-time':
#              #           print s['title']
#                         txt = s['title']
#                     elif s['class'][1].find('ball') != -1:
#                         txt = u'ГОЛ!'
#             else:
#                 txt = s.text
#             link = link + u' |  ' + txt
#         links.append(link)
#         print link


#print tag_reviews


