from unicodedata import category
from django.shortcuts import render
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from sa.models import Actuator, This, That, Rule, User
import uuid
from util.precisiation import Precisiation
from sentence_transformers import SentenceTransformer
from scipy import spatial
import spacy
import editdistance

nlp = spacy.load('en_core_web_sm',disable=['ner','textcat'])
# model_sbert = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
model_sbert = SentenceTransformer('all-MiniLM-L12-v2')

# Create your views here.
def index(request):
    return HttpResponse("Hello. You're at the smart assistant index.")


def ifttt(request, rule = None, user_id = None):
    new_id = False
    if user_id == None:
        user_id = request.COOKIES.get("Django_test_cookie")
        if user_id is None:
            # Cookie is not set, set it to random user ID
            new_id = True
            user_id = uuid.uuid4()

    actuators = Actuator.objects.all()

    context = {"user_id" : user_id, "actuators" : actuators, "rule": rule}
    response = render(request, "sa/ifttt.html", context)
    
    if new_id:
        response.set_cookie("Django_test_cookie", user_id)

    return response

def assistant(request, typ = "A", user_id = None, query = None, message = None):
    new_id = False
    if user_id == None:
        user_id = request.COOKIES.get("Django_test_cookie")
        if user_id is None:
            # Cookie is not set, set it to random user ID
            new_id = True
            user_id = uuid.uuid4()

    context = {"user_id" : user_id, "message": message, "query": query, "typ": typ}
    response = render(request, "sa/assistant.html", context)
    
    if new_id:
        response.set_cookie("Django_test_cookie", user_id)

    return response

def add_ifttt(request, user_id):
    this_sentence = request.POST["this"]
    that_actuator = request.POST["actuator"]
    that_value = request.POST["value"]
    
    tokens = nlp(this_sentence)

    var = ""
    for i,token in enumerate(tokens):
        if ((token.tag_ in ["JJ", "JJR", "JJS", "PDT", "RB", "RBR", "RBS"] or 
            (var == "" and i == len(tokens)-1 and (nlp(token.text)[0].pos_ == "ADJ" or nlp(token.text)[0].pos_ == "ADV"))) and 
            token.text not in ["here", "there", "in"]):
            var = token.text

    p = Precisiation()
    cat = p.get_category([var])

    this = This(originalcommand = this_sentence, command = this_sentence.replace(var, cat), variable = var, category = cat)
    act = Actuator.objects.get(id=that_actuator)
    that = That(actuator = act, value = that_value)
    this.save()
    that.save()

    try:
        user = User.objects.get(userId = user_id)
    except ObjectDoesNotExist:
        user = User(userId = user_id)
        user.save()

    rule = Rule(this = this, that = that, user = user)
    rule.save()

    return ifttt(request, f"IF SAY '{this_sentence}' THEN SET {act} to {that_value} {act.units}")

def execute_query(request, typ = "A", user_id=None):
    # If the query has been done to the assistant A (the fuzzy one!)
    if typ == "A":
        query = request.POST["query"]

        # Tokenize and find POS
        tokens = nlp(query)

        adj = ""
        
        for i,token in enumerate(tokens):
            if ((token.tag_ in ["JJ", "JJR", "JJS", "PDT", "RB", "RBR", "RBS"] or 
                (adj == "" and i == len(tokens)-1 and (nlp(token.text)[0].pos_ == "ADJ" or nlp(token.text)[0].pos_ == "ADV"))) and 
                token.text not in ["here", "there", "in"]):
                    print(token)
                    adj = token.text

        # Remove POS and encode with sBERT
        p = Precisiation(db_file="./synonyms.db")
        cat = p.get_category([adj])
        query_c = query.replace(adj, cat)
        encoded_query = model_sbert.encode(query_c)

        # Find best matching query, giving the priority to those with the same category
        maxi = ("", 0)
        for r in Rule.objects.filter(user__userId = user_id).filter(this__category = cat):
            s = r.this.command
            sim = 1 - spatial.distance.cosine(model_sbert.encode(s),encoded_query)
            if sim > maxi[1]:
                maxi = (r, sim)

        # If nothing good enough was found, try to search also in other categories
        if maxi[1] < 0.5:
            maxi = ("", 0)
            for r in Rule.objects.filter(user__userId = user_id):
                s = r.this.command
                sim = 1 - spatial.distance.cosine(model_sbert.encode(s),encoded_query)
                if sim > maxi[1]:
                    maxi = (r, sim)
            
            # If no matching category, return error and let user repeat the query
            if maxi[1] < 0.5:
                # Return message unknown command and let try another query
                return assistant(request, typ = typ, query = query, message = "Unknown query, please try with another wording.")

        # Precisiate the word from the ground truth and that from the query
        adj_gt = maxi[0].this.variable
        cat_gt = maxi[0].this.category
        target_gt = maxi[0].that.value
        target_range = (maxi[0].that.actuator.minimum, maxi[0].that.actuator.maximum)
        target_units = maxi[0].that.actuator.units

        prec_gt = p.precisiate_v2(adj_gt, cat_gt)
        distmax = abs(2 * abs(target_gt-target_range[0]) - abs(target_range[1]-target_range[0]))

        if adj.lower() == "medium":
            prec = (0.5,)
        else:
            prec = p.precisiate_v2(adj, cat)

        dist = abs(prec[0]-prec_gt[0])*distmax

        target_result = target_gt - dist if (target_gt - dist >= target_range[0] 
            and target_gt - dist < target_range[1]) else target_gt + dist

        target_result = round(target_result, 1)

        return assistant(request, typ = typ, user_id = user_id, query = query, message =f"Okay, I will set {maxi[0].that.actuator} to {target_result} {target_units}")
    
    # The request has been done to the "normal" assistant
    else:
        query = request.POST["query"]

        # Find best matching query with string edit distance
        mini = ("", 100)
        for r in Rule.objects.all():
            s = r.this.originalcommand
            dist = editdistance.eval(s, query)

            if dist < mini[1]:
                mini = (r, dist)

        # If nothing good enough was found, unknown query, otherwise return matched query
        if mini[1] > 4:
            return assistant(request, typ = typ, user_id = user_id, query = query, message = "Unknown query, please try with another wording.")

        target_gt = mini[0].that.value
        target_units = mini[0].that.actuator.units

        return assistant(request, typ = typ, user_id = user_id, query = query, message =f"Okay, I will set {mini[0].that.actuator} to {target_gt} {target_units}")