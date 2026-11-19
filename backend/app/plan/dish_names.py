"""Dish names in Hindi and Telugu script: dish id | Hindi | Telugu.

Regional dishes keep their own name, written in each script (gongura pappu is గోంగూర పప్పు in Telugu and
गोंगुरा पप्पु in Hindi), because that is how people know them.
"""

_TABLE = """
steamed_rice|चावल|అన్నం
brown_rice|ब्राउन चावल|బ్రౌన్ రైస్
phulka|फुलका (बिना तेल की रोटी)|పుల్కా
chapati|चपाती|చపాతీ
whole_wheat_bread|गेहूँ की ब्रेड|గోధుమ బ్రెడ్
oats_milk|दूध में ओट्स|పాలలో ఓట్స్
poha|पोहा|అటుకుల ఉప్మా
rava_upma|रवा उपमा|రవ్వ ఉప్మా
moong_dal_khichdi|मूंग दाल खिचड़ी|పెసరపప్పు కిచిడీ
veg_pulao|वेज पुलाव|వెజ్ పులావ్
curd|दही|పెరుగు
buttermilk|छाछ|మజ్జిగ
milk|दूध|పాలు
fortified_milk|विटामिन D वाला दूध (+F)|విటమిన్ D పాలు (+F)
tea|दूध वाली चाय|పాల టీ
filter_coffee|फ़िल्टर कॉफ़ी|ఫిల్టర్ కాఫీ
lemon_water|नींबू पानी|నిమ్మరసం
boiled_egg|उबला अंडा|ఉడికించిన గుడ్డు
onion_omelette|प्याज़ ऑमलेट|ఉల్లి ఆమ్లెట్
kachumber|खीरा-गाजर सलाद|దోసకాయ-క్యారెట్ సలాడ్
moong_sprouts|अंकुरित मूंग सलाद|మొలకెత్తిన పెసల సలాడ్
roasted_gram|भुने चने|పుట్నాలు
mushroom_curry|मशरूम करी|పుట్టగొడుగుల కూర
banana|केला|అరటిపండు
guava|अमरूद|జామపండు
apple|सेब|ఆపిల్
orange|संतरा|కమలాపండు
papaya|पपीता|బొప్పాయి
watermelon|तरबूज़|పుచ్చకాయ
pomegranate|अनार|దానిమ్మ
sapota|चीकू|సపోటా
mango|आम|మామిడిపండు
grapes|अंगूर|ద్రాక్ష
jonna_rotte|ज्वार की रोटी|జొన్న రొట్టె
sajja_rotte|बाजरे की रोटी|సజ్జ రొట్టె
ragi_sankati|रागी मुद्दा (संकटी)|రాగి సంకటి
samala_annam|सामा (कुटकी) चावल|సామల అన్నం
idli|इडली|ఇడ్లీ
plain_dosa|डोसा|దోశ
masala_dosa|मसाला डोसा|మసాలా దోశ
onion_uttapam|प्याज़ उत्तपम|ఉల్లి ఊతప్పం
ragi_dosa|रागी डोसा|రాగి దోశ
pesarattu|पेसरट्टू (हरी मूंग का डोसा)|పెసరట్టు
sarva_pindi|सर्व पिंडी|సర్వపిండి
uggani|उग्गानी (मुरमुरे का उपमा)|ఉగ్గాని
semiya_upma|सेवई उपमा|సేమియా ఉప్మా
medu_vada|मेदु वड़ा|మినప గారెలు
punugulu|पुनुगुलु|పునుగులు
mirchi_bajji|मिर्ची बज्जी|మిర్చి బజ్జీ
onion_pakoda|प्याज़ पकौड़ा|ఉల్లిపాయ పకోడీ
guggillu|घुघनी (मसालेदार चने)|గుగ్గిళ్లు
boiled_peanuts|उबली मूंगफली|ఉడికించిన పల్లీలు
roasted_corn|भुना भुट्टा|కాల్చిన మొక్కజొన్న
sakinalu|सकिनालु|సకినాలు
borugula_mixture|मुरमुरा भेल|బొరుగుల మిక్చర్
pulihora|इमली चावल (पुलिहोरा)|చింతపండు పులిహోర
lemon_rice|नींबू चावल|నిమ్మకాయ పులిహోర
tomato_rice|टमाटर चावल|టమాటా అన్నం
curd_rice|दही चावल|దద్దోజనం
bagara_annam|बघारा चावल|బగారా అన్నం
chicken_biryani|चिकन बिरयानी|చికెన్ బిర్యానీ
mutton_biryani|मटन बिरयानी|మటన్ బిర్యానీ
tomato_pappu|टमाटर दाल|టమాటా పప్పు
palakura_pappu|पालक दाल|పాలకూర పప్పు
thotakura_pappu|चौलाई दाल|తోటకూర పప్పు
gongura_pappu|गोंगुरा दाल|గోంగూర పప్పు
menthikura_pappu|मेथी दाल|మెంతికూర పప్పు
dosakaya_pappu|पीली ककड़ी की दाल (दोसकाया पप्पु)|దోసకాయ పప్పు
mamidikaya_pappu|कच्चे आम की दाल|మామిడికాయ పప్పు
mudda_pappu|घी के साथ सादी दाल|ముద్దపప్పు
pesara_pappu|मूंग दाल|పెసరపప్పు
dalcha|दालचा|దాల్చా
sambar|सांभर|సాంబారు
pappu_charu|पप्पु चारु (पतली दाल)|పప్పుచారు
rasam|रसम|చారు
pachi_pulusu|कच्ची इमली का रसम (पच्ची पुलुसु)|పచ్చిపులుసు
mukkala_pulusu|सब्ज़ियों का पुलुसु|ముక్కల పులుసు
majjiga_pulusu|छाछ की कढ़ी (मज्जिगा पुलुसु)|మజ్జిగ పులుసు
ulava_charu|कुलथी का रसम (उलवा चारु)|ఉలవచారు
ragi_java_salt|छाछ वाली रागी जावा|మజ్జిగతో రాగి జావ
ragi_java_milk|दूध-गुड़ वाली रागी जावा|పాలు బెల్లంతో రాగి జావ
bendakaya_fry|भिंडी फ्राई|బెండకాయ వేపుడు
gutti_vankaya|भरवां बैंगन (गुत्ति वंकाया)|గుత్తి వంకాయ కూర
vankaya_tomato|बैंगन-टमाटर सब्ज़ी|వంకాయ టమాటా కూర
aloo_fry|आलू फ्राई|బంగాళదుంప వేపుడు
dondakaya_fry|कुंदरू फ्राई|దొండకాయ వేపుడు
beerakaya_kura|तुरई की सब्ज़ी|బీరకాయ కూర
sorakaya_kura|लौकी चना दाल|సొరకాయ శనగపప్పు కూర
kakarakaya_fry|करेला फ्राई|కాకరకాయ వేపుడు
cabbage_kura|पत्ता गोभी की सब्ज़ी|క్యాబేజీ కూర
beans_kura|बीन्स की सब्ज़ी|బీన్స్ కూర
thotakura_vepudu|चौलाई की सूखी सब्ज़ी|తోటకూర వేపుడు
chikkudukaya_kura|सेम की सब्ज़ी|చిక్కుడుకాయ కూర
aratikaya_vepudu|कच्चे केले की फ्राई|అరటికాయ వేపుడు
kanda_vepudu|ज़िमीकंद फ्राई|కంద వేపుడు
chamadumpa_pulusu|अरबी इमली ग्रेवी|చామదుంప పులుసు
goruchikkudu_kura|ग्वार फली की सब्ज़ी|గోరుచిక్కుడు కూర
mirchi_ka_salan|मिर्ची का सालन|మిర్చి కా సాలన్
egg_curry|अंडा करी|కోడిగుడ్డు కూర
egg_bhurji|अंडा भुर्जी|గుడ్డు పొరటు
chicken_curry|चिकन करी|కోడి కూర
natu_kodi_pulusu|देसी चिकन करी|నాటుకోడి పులుసు
chicken_fry|चिकन फ्राई|కోడి వేపుడు
chicken_liver_fry|चिकन कलेजी फ्राई|కలేజా వేపుడు
mutton_curry|मटन करी|మాంసం కూర
gongura_mamsam|गोंगुरा मटन|గోంగూర మాంసం
chepala_pulusu|इमली वाली मछली करी|చేపల పులుసు
fish_fry|मछली फ्राई|చేపల వేపుడు
royyala_iguru|झींगा करी|రొయ్యల ఇగురు
kobbari_pachadi|नारियल चटनी|కొబ్బరి పచ్చడి
palli_pachadi|मूंगफली चटनी|పల్లీ పచ్చడి
tomato_pachadi|टमाटर चटनी|టమాటా పచ్చడి
gongura_pachadi|गोंगुरा चटनी|గోంగూర పచ్చడి
allam_pachadi|अदरक चटनी|అల్లం పచ్చడి
pudina_pachadi|पुदीना चटनी|పుదీనా పచ్చడి
beerakaya_pachadi|तुरई की चटनी|బీరకాయ పచ్చడి
vankaya_pachadi|भुने बैंगन की चटनी|వంకాయ పచ్చడి
kandi_podi|घी के साथ दाल पोडी|నెయ్యితో కంది పొడి
karivepaku_podi|करी पत्ता पोडी|కరివేపాకు పొడి
perugu_pachadi|दही रायता|పెరుగు పచ్చడి
bobbatlu|पूरन पोली (बोब्बट्लु)|బొబ్బట్లు
ariselu|अरिसेलु|అరిసెలు
semiya_payasam|सेवई की खीर|సేమియా పాయసం
chakkera_pongali|मीठा पोंगल|చక్కెర పొంగలి
sunnundalu|उड़द दाल के लड्डू|సున్నుండలు
ven_pongal|वेन पोंगल|వెన్ పొంగల్ (కట్టె పొంగలి)
adai|अडै (मिश्रित दाल डोसा)|అడై
rava_dosa|रवा डोसा|రవ్వ దోశ
kuzhi_paniyaram|पनियारम|పొంగనాలు
idiyappam|इडियप्पम|ఇడియప్పం
thengai_sadam|नारियल चावल|కొబ్బరి అన్నం
kara_kuzhambu|कारा कुलंबु (इमली ग्रेवी)|కార కుళంబు
chow_chow_kootu|चाउ चाउ कूटू|చౌ చౌ కూటు
keerai_masiyal|चौलाई मसियल|తోటకూర మసియల్
chettinad_chicken|चेट्टिनाड चिकन करी|చెట్టినాడ్ చికెన్ కూర
pepper_chicken|पेपर चिकन|పెప్పర్ చికెన్
meen_kuzhambu|मीन कुलंबु (मछली करी)|మీన్ కుళంబు (చేపల కూర)
mutton_kuzhambu|मटन कुलंबु|మటన్ కుళంబు
parotta|परोटा|పరోటా
rava_kesari|रवा केसरी|రవ్వ కేసరి
kozhukattai|मीठे कोलुकट्टै (मोदक)|కుడుములు (మోదకాలు)
matta_rice|केरल मट्टा चावल|కేరళ మట్ట బియ్యం అన్నం
puttu|पुट्टु|పుట్టు
appam|अप्पम|అప్పం
kappa_puzhukku|कप्पा (टैपिओका मैश)|కప్ప (కర్రపెండలం)
kanji_payar|कांजी और हरी मूंग|గంజి, పెసలు
kadala_curry|काले चने की करी (कडला करी)|కడల కూర (నల్ల శనగల కూర)
veg_stew|वेज स्ट्यू (इष्टु)|వెజ్ స్టూ (ఇష్టు)
chicken_stew|केरल चिकन स्ट्यू|కేరళ చికెన్ స్టూ
kerala_fish_curry|केरल मछली करी|కేరళ చేపల కూర
meen_varuthathu|केरल मछली फ्राई|కేరళ చేపల వేపుడు
cabbage_thoran|पत्ता गोभी तोरन|క్యాబేజీ తోరన్
beans_thoran|बीन्स तोरन|బీన్స్ తోరన్
olan|ओलन|ఓలన్
erissery|एरिशेरी (कद्दू-लोबिया)|ఎరిస్సేరి (గుమ్మడి-బొబ్బర్లు)
avial|अवियल|అవియల్
parippu_curry|केरल दाल (परिप्पु)|కేరళ పప్పు (పరిప్పు)
beef_ularthiyathu|केरल बीफ़ फ्राई|కేరళ బీఫ్ వేపుడు
egg_roast|केरल एग रोस्ट|కేరళ ఎగ్ రోస్ట్
pazham_pori|केले के पकौड़े (पझम पोरी)|అరటి బజ్జీ (పళం పొరి)
banana_chips|केले के चिप्स|అరటి చిప్స్
unniyappam|उन्नियप्पम|ఉన్నియప్పం
palada_payasam|पालडा पायसम|పాలడ పాయసం
coconut_water|नारियल पानी|కొబ్బరి నీళ్లు
bisi_bele_bath|बिसी बेले भात|బిసి బేళే బాత్
vangi_bath|बैंगन चावल (वांगी भात)|వాంగీ బాత్ (వంకాయ అన్నం)
akki_rotti|चावल के आटे की रोटी (अक्की रोटी)|అక్కి రొట్టె
ragi_rotti|रागी रोटी|రాగి రొట్టె
neer_dosa|नीर डोसा|నీర్ దోశ
set_dosa|सेट डोसा|సెట్ దోశ
rava_idli|रवा इडली|రవ్వ ఇడ్లీ
kosambari|मूंग दाल सलाद (कोसंबरी)|కోసంబరి
tovve|कर्नाटक दाल (तोव्वे)|తొవ్వే (కర్ణాటక పప్పు)
kori_gassi|मंगलोरी चिकन करी (कोरी गस्सी)|కోరి గస్సీ (మంగళూరు చికెన్ కూర)
mysore_pak|मैसूर पाक|మైసూర్ పాక్
plain_paratha|सादा पराठा|పరాటా
aloo_paratha|आलू पराठा|ఆలూ పరాటా
gobi_paratha|गोभी पराठा|గోబీ పరాటా
mooli_paratha|मूली पराठा|ముల్లంగి పరాటా
makki_roti|मक्की की रोटी|మొక్కజొన్న రొట్టె
puri|पूरी|పూరీ
bhatura|भटूरा|భటూరా
jeera_rice|जीरा चावल|జీరా రైస్
matar_pulao|मटर पुलाव|బఠాణీ పులావ్
besan_chilla|बेसन चीला|శనగపిండి చీలా
moong_chilla|मूंग दाल चीला|పెసరపప్పు చీలా
namkeen_dalia|नमकीन दलिया|ఉప్పు దలియా (గోధుమ రవ్వ)
meetha_dalia|मीठा दलिया|తీపి దలియా
dal_tadka|दाल तड़का|దాల్ తడ్కా
dhuli_moong_dal|धुली मूंग दाल|పెసరపప్పు (ఉత్తర భారత పద్ధతి)
masoor_dal|मसूर दाल|మసూర్ పప్పు
chana_dal|चना दाल|శనగపప్పు
dal_makhani|दाल मखनी|దాల్ మఖనీ
rajma|राजमा|రాజ్మా
chole|छोले|చోలే
kala_chana|काले चने की करी|నల్ల శనగల కూర
sabut_moong|साबुत मूंग दाल|పెసల కూర
lobia|लोबिया करी|బొబ్బర్ల కూర
kadhi_pakora|कढ़ी पकौड़ा|కఢీ పకోడా
aloo_gobi|आलू गोभी|ఆలూ గోబీ
aloo_matar|आलू मटर|ఆలూ మటర్
jeera_aloo|जीरा आलू|జీరా ఆలూ
bhindi_masala|भिंडी मसाला|బెండకాయ మసాలా
baingan_bharta|बैंगन भरता|వంకాయ భర్తా
palak_paneer|पालक पनीर|పాలక్ పనీర్
matar_paneer|मटर पनीर|మటర్ పనీర్
paneer_butter_masala|पनीर बटर मसाला|పనీర్ బటర్ మసాలా
kadai_paneer|कड़ाही पनीर|కడాయి పనీర్
paneer_bhurji|पनीर भुर्जी|పనీర్ బుర్జీ
mix_veg|मिक्स वेज सब्ज़ी|మిక్స్ వెజ్ కూర
lauki_sabzi|लौकी की सब्ज़ी|సొరకాయ కూర
tinda_masala|टिंडा मसाला|టిండా మసాలా
arbi_fry|अरबी फ्राई|చామదుంప వేపుడు
karela_pyaz|करेला प्याज़|కాకరకాయ ఉల్లి కూర
sarson_ka_saag|सरसों का साग|ఆవాకు కూర (సర్సోం కా సాగ్)
gajar_matar|गाजर मटर|క్యారెట్ బఠాణీ కూర
patta_gobhi_matar|पत्ता गोभी मटर|క్యాబేజీ బఠాణీ కూర
methi_aloo|मेथी आलू|మెంతికూర ఆలూ
khatta_meetha_kaddu|खट्टा मीठा कद्दू|పుల్ల తీపి గుమ్మడి కూర
soya_matar|सोया चंक्स मटर|సోయా బఠాణీ కూర
anda_curry|अंडा करी|ఉత్తర భారత గుడ్డు కూర
chicken_curry_north|चिकन करी (उत्तर भारतीय)|చికెన్ కూర (ఉత్తర భారత)
butter_chicken|बटर चिकन|బటర్ చికెన్
kadai_chicken|कड़ाही चिकन|కడాయి చికెన్
mutton_curry_north|मटन करी (उत्तर भारतीय)|మటన్ కూర (ఉత్తర భారత)
rogan_josh|रोगन जोश|రోగన్ జోష్
keema_matar|कीमा मटर|కీమా మటర్
samosa|समोसा|సమోసా
aloo_tikki|आलू टिक्की|ఆలూ టిక్కీ
chana_chaat|चना चाट|శనగల చాట్
fruit_chaat|फ्रूट चाट|ఫ్రూట్ చాట్
boondi_raita|बूंदी रायता|బూందీ రైతా
cucumber_raita|खीरा रायता|దోసకాయ రైతా
hari_chutney|हरी चटनी|పుదీనా కొత్తిమీర చట్నీ
sweet_lassi|मीठी लस्सी|తీపి లస్సీ
haldi_doodh|हल्दी वाला दूध|పసుపు పాలు
rice_kheer|चावल की खीर|బియ్యం పాయసం
gajar_halwa|गाजर का हलवा|క్యారెట్ హల్వా
sooji_halwa|सूजी का हलवा|రవ్వ హల్వా
besan_ladoo|बेसन के लड्डू|శనగపిండి లడ్డు
gulab_jamun|गुलाब जामुन|గులాబ్ జామూన్
sabudana_khichdi|साबूदाना खिचड़ी|సగ్గుబియ్యం కిచిడీ
thalipeeth|थालीपीठ|థాలీపీఠ్
varan|वरण (सादी दाल)|వరణ్ (సాదా పప్పు)
amti|आमटी|ఆమ్టీ
matki_usal|मटकी उसळ|మట్కీ ఉసళ్ (మట్కీ కూర)
pithla|पिठला|పిఠ్లా (శనగపిండి కూర)
batata_bhaji|बटाटा भाजी|బటాటా భాజీ (ఆలూ వేపుడు)
sol_kadhi|सोल कढ़ी|సోల్ కఢీ
shrikhand|श्रीखंड|శ్రీఖండ్
dhokla|ढोकला|ఢోక్లా
thepla|मेथी थेपला|మెంతి థేప్లా
gujarati_dal|गुजराती दाल|గుజరాతీ పప్పు
gujarati_kadhi|गुजराती कढ़ी|గుజరాతీ కఢీ
undhiyu|उंधियू|ఉంధియూ
dal_baati|दाल बाटी|దాల్ బాటీ
gatte_ki_sabzi|गट्टे की सब्ज़ी|గట్టే కీ సబ్జీ
goan_fish_curry|गोवा फिश करी|గోవా చేపల కూర
machher_jhol|माछेर झोल (मछली-आलू करी)|మాఛేర్ ఝోల్ (చేప-బంగాళదుంప కూర)
shorshe_ilish|सरसों हिल्सा (शोर्षे इलिश)|ఆవాలతో ఇలిష్ చేప
cholar_dal|छोलार दाल|ఛోలార్ దాల్ (శనగపప్పు)
aloo_posto|आलू पोस्तो|ఆలూ పోస్తో (గసగసాల బంగాళదుంప)
shukto|शुक्तो|శుక్తో
begun_bhaja|बेगुन भाजा (तला बैंगन)|బేగున్ భాజా (వంకాయ వేపుడు)
luchi|लुची|లుచీ
mishti_doi|मिष्टी दोई|మిష్టీ దోయ్ (తీపి పెరుగు)
rosogolla|रसगुल्ला|రసగుల్లా
dalma|दालमा|దాల్మా
santula|संतुला|సంతుల
litti_chokha|लिट्टी चोखा|లిట్టీ చోఖా
sattu_drink|सत्तू का घोल|సత్తు పానీయం
masor_tenga|मासोर टेंगा (खट्टी मछली करी)|మాసోర్ టెంగా (పుల్లని చేపల కూర)
aloo_pitika|आलू पितिका|ఆలూ పితిక
pork_bamboo_shoot|बांस की कोंपल के साथ पोर्क|వెదురు చిగుళ్లతో పోర్క్
veg_momos|वेज मोमोज़|వెజ్ మోమోస్
chicken_momos|चिकन मोमोज़|చికెన్ మోమోస్
thukpa|थुकपा|థుక్పా
chirer_pulao|चिड़े का पुलाव|అటుకుల పులావ్
"""

NAMES = {}
for _line in _TABLE.strip().splitlines():
    _id, _hi, _te = _line.split("|")
    NAMES[_id] = {"hi": _hi, "te": _te}
