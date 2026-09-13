"""Caption-only assistant candidates authored before any expanded model calls.

Only direct positive claims. Empty exclusions do not assert full scope annotation.
Groups/parts/compound names remain reviewable protocol choices, not human gold.
"""


def S(text,attrs=()):
    entities=[]
    for part in text.split(';'):
        xs=part.split('|')
        key=xs[0];name=key.replace('_',' ') if len(xs)==2 else xs[1]
        entities.append((key,name,xs[-1]))
    return (entities,list(attrs))


SPECS={
'326667':{
 'original':S('bird|bird;water|water;wing|wing|wings;rock|rock|rocks;air|air',[
     ('bird','size','large','large bird','large')]),
 'steer':S('bird|bird;lake|lake')},
'352377':{
 'original':S('fruit|fruit|fruits;apple|apple|apples;orange|orange|oranges'),
 'steer':S('fruit|fruit;apple_green|apple|Some of the apples;apple_yellow|apple|others;orange|orange|oranges;banana_yellow|banana|some being yellow;banana_green|banana|others being green',[
     ('apple_green','color','green','Some of the apples are green','green'),
     ('apple_yellow','color','yellow','while others are yellow','yellow'),
     ('banana_yellow','color','yellow','some being yellow','yellow'),
     ('banana_green','color','green','others being green','green')])},
'195269':{
 'original':S('man|man;boy|boy;kite|kite;string|kite string;sky|sky;beach|beach;house|house|houses;car|car',[
     ('beach','material','sand','sandy beach','sandy')]),
 'steer':S('person1|person|One person;person2|person|another person;kite|kite;string1|kite string|string;string2|kite string|another person is holding a kite string;sky|sky;beach|beach;hoodie|hoodie;shorts|shorts',[
     ('beach','material','sand','sandy beach','sandy')])},
'69584':{
 'original':S('airplane|airplane;sky|sky;wing|wing|wings;cloud|cloud|clouds;air|air',[
     ('airplane','size','large','large airplane','large')]),
 'steer':S('airplane|airplane;sky|sky',[
     ('airplane','size','large','large airplane','large')])},
'317188':{
 'original':S('woman|woman;glasses|glasses;beach|beach;cell_phone|cell phone;hand|hand;sweater|sweater',[
     ('sweater','color','pink','pink sweater','pink')]),
 'steer':S('woman|woman;glasses|glasses;cell_phone|cell phone;beach|beach',[
     ('cell_phone','color','purple','purple cell phone','purple'),
     ('beach','material','sand','sandy beach','sandy')])},
'373677':{
 'original':S('clock_tower|clock tower;roof|roof;building|building;clock|clock;facade|facade;plant|potted plant|potted plants',[
     ('clock_tower','size','large','large clock tower','large'),
     ('roof','color','red','red roof','red'),
     ('facade','material','wood','wooden facade','wooden')]),
 'steer':S('clock_tower|clock tower;clock|clock;person_left|person|one on the left side;person_right|person|another on the right side;building|building;public_area|public area')},
'279634':{
 'original':S('child|child;sidewalk|sidewalk;snowboard|snowboard;hand|hand|hands;people|people;car_left|car|one on the left side;car_right|car|the other on the right side;backpack_center|backpack|one near the center;backpack_right|backpack|the other towards the right side'),
 'steer':S('child|child;helmet|helmet;snowboard|snowboard;sidewalk|sidewalk;hand|hand|hands;people|people;winter_gear|winter gear;car|car')},
'45094':{
 'original':S('man|man;cap|baseball cap|baseball cap;table|dining table|dining table;glass1|glass|a glass of red wine;wine|wine;glass2|wine glass|wine glass;person2|person|Another person;nose|nose;chair|chair|chairs;bottle|bottle|bottles;cup|cup',[
     ('wine','color','red','red wine','red')]),
 'steer':S('man|man;cap|cap;glass1|glass|glass;wine|wine;shirt|shirt',[
     ('shirt','color','white','white shirt','white')])},
'381925':{
 'original':S('girl|girl;bench|bench;dog|dog;arm|arm|arms;hat|hat;scarf|scarf;rock|rock|rocks',[
     ('bench','material','wood','wooden bench','wooden'),
     ('rock','size','large','large rocks','large')]),
 'steer':S('girl|girl;hat|hat;scarf|scarf;bench|bench;dog|dog;remote_control|remote control;hand|hand;grassy_area|grassy area',[
     ('bench','material','wood','bench is made of wood','wood')])},
'54264':{
 'original':S('lion_statue|lion statue;store|store;fence|fence;sign_fence|sign|a sign on the fence;sign_building|sign|a prominent sign on the side of the building;building|building;car|car;person|person',[
     ('lion_statue','size','large','large white lion statue','large'),
     ('lion_statue','color','white','white lion statue','white')]),
 'steer':S('lion_statue|lion statue;store|store',[
     ('lion_statue','size','large','large white lion statue','large'),
     ('lion_statue','color','white','white lion statue','white'),
     ('lion_statue','material','marble','lion statue is made of marble','marble')])},
'256003':{
 'original':S('train_set|model train set|model train set;train|train;track|track|tracks;building|building;barn|barn;tractor|tractor;person_middle|person|one near the middle;person_right|person|the other closer to the right side',[
     ('building','size','small','small building','small'),
     ('tractor','size','small','small tractor','small')]),
 'steer':S('train|model train|model train;track|track|tracks')},
'462687':{
 'original':S('people|people;pizza|pizza;pizza_slice|pizza slice|slices;table|table;men|man|men;women|woman|women;bench|bench;apple_left|apple|one on the left side of the bench;apple_right|apple|another on the right side;clock|clock;wall|wall;handbag|handbag;ground|ground'),
 'steer':S('people|people;food|food;sunglasses|sunglasses;fruit|fruit;watch|watch|watches')},
'450500':{
 'original':S('street|street;people|people;sidewalk|sidewalk;car|car|cars;traffic_light|traffic light;girl|girl;shirt|shirt;man|man;stool|stool;handbag|handbag|handbags;backpack|backpack',[
     ('shirt','color','pink','pink shirt','pink'),
     ('stool','size','small','small stool','small')]),
 'steer':S('street|street;people|people;sidewalk|sidewalk;car|car|cars;traffic_light|traffic light;intersection|intersection;palm_tree|palm tree|palm trees;girl|girl;vehicle|vehicle|vehicles')},
'69946':{
 'original':S('marina|marina;boat|boat|boats;water|water;shore|shore;car|car|cars;person|person'),
 'steer':S('marina|marina;boat|boat|boats;water|water;grassy_area|grassy area;people|people')},
'265462':{
 'original':S('skateboarder|skateboarder|skateboarders;skateboard|skateboard|skateboards;stairs|stairs'),
 'steer':S('skateboarder|skateboarder|skateboarders;skate_park|skate park;shirt|shirt|shirts;jeans|jeans;skateboard|skateboard|skateboards',[
     ('shirt','color','black','black shirts','black')])},
'303499':{
 'original':S('rider|rider|riders;coat|coat|coats;horse_left|horse|one horse on the left side;horse_middle|horse|another in the middle;horse_right|horse|two more on the right side;courtyard|courtyard',[
     ('coat','color','red','red coats','red')]),
 'steer':S('rider1|rider|one person;rider2|rider|the other person;coat|coat|coats;horse_black|horse|black horse;horse_brown|horse|brown horse;public_area|public area',[
     ('coat','color','red','red coats','red'),
     ('horse_black','color','black','black horse','black'),
     ('horse_brown','color','brown','brown horse','brown')])},
'316617':{
 'original':S('person_left|person|one person standing closer to the left side;person_middle|person|another person in the middle;person_right|person|the third person on the right side;woods|woods;frisbee_left|frisbee|one frisbee located near the left person;frisbee_middle|frisbee|another frisbee in the middle;frisbee_right|frisbee|the third frisbee near the right person;handbag_left|handbag|One handbag;handbag_right|handbag|the other handbag'),
 'steer':S('people|people;wooded_area|wooded area;shirt_red|shirt|red shirt;shirt_white|shirt|white shirt;ground|ground;frisbee|frisbee',[
     ('shirt_red','color','red','red shirt','red'),
     ('shirt_white','color','white','white shirt','white')])},
'519838':{
 'original':S('park|park;bicycle|bicycle;tree|tree;dog|dog;car|car|cars;person_left|person|one closer to the left side;person_right|person|the other near the right side;backpack|backpack;ground|ground'),
 'steer':S('park|park;tree|tree;bicycle|bicycle;dog_left|dog|one dog;dog_right|dog|the other dog')},
'565761':{
 'original':S('room|room;men|man|men;table|table;suit|suit;tie|tie;attire|attire;chair|chair|chairs;people|people;television|television;wall|wall;plant|potted plant|potted plant',[
     ('room','size','large','large room','large')]),
 'steer':S('room|room;people|people;chair|chair|chairs;bench|bench|benches;television|television screen|television screen;table|table;cup|cup|cups;bowl|bowl',[
     ('room','size','large','large room','large')])},
'483723':{
 'original':S('beach|beach;men|man|men;umbrella|umbrella;surfboard|surfboard|surfboards;handbag|handbag;cell_phone|cell phone',[
     ('umbrella','size','large','large umbrella','large')]),
 'steer':S('beach|beach;man1|man|One man;man2|man|the other man;sheltered_area|sheltered area;clothing|clothing;hammock|hammock;chair|chair',[
     ('clothing','color','blue','blue clothing','blue')])},
}

# Explicitly freeze uncertain identity/granularity components, rather than guess matches.
AMBIGUITIES={
'326667':[{'original':['water'],'steer':['lake']}],
'352377':[{'original':['apple'],'steer':['apple_green','apple_yellow']}],
'195269':[{'original':['man','boy'],'steer':['person1','person2']},
          {'original':['string'],'steer':['string1','string2']}],
'279634':[{'original':['car_left','car_right'],'steer':['car']}],
'462687':[{'original':['people','men','women'],'steer':['people']},
          {'original':['pizza','pizza_slice'],'steer':['food']},
          {'original':['apple_left','apple_right'],'steer':['fruit']}],
'450500':[{'original':['shirt'],'steer':[]}],
'69946':[{'original':['person'],'steer':['people']}],
'303499':[{'original':['rider'],'steer':['rider1','rider2']},
          {'original':['horse_left','horse_middle','horse_right'],'steer':['horse_black','horse_brown']},
          {'original':['courtyard'],'steer':['public_area']}],
'316617':[{'original':['person_left','person_middle','person_right'],'steer':['people']},
          {'original':['frisbee_left','frisbee_middle','frisbee_right'],'steer':['frisbee']},
          {'original':['woods'],'steer':['wooded_area']}],
'519838':[{'original':['dog'],'steer':['dog_left','dog_right']}],
'565761':[{'original':['men','people'],'steer':['people']}],
'483723':[{'original':['men'],'steer':['man1','man2']},
          {'original':['umbrella'],'steer':['sheltered_area']}],
}
