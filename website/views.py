from flask import Blueprint,render_template,request,flash,redirect,url_for
from sqlalchemy import desc
from flask_login import current_user,login_required
from .models import *
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime


views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template('home.html', user = current_user)

# @views.route('api/sponsor/dashboard')
# @login_required
# def dashboard():
#     sponsor = Sponsor.query.get(current_user.id)

### SPONSOR ROUTES ###
@views.route('sponsor/dashboard')
@login_required
def sponsor_dashboard():
    sponsor = Sponsor.query.get(current_user.id)
    campaigns = [campaign for campaign in sponsor.campaigns if (campaign.end_date > datetime.now().date()) and (campaign.start_date < datetime.now().date()) and (campaign.flagged == 'False')]
    current_date = datetime.now().date()
    
    new_nego = Negotiation.query.filter_by(sponsor_id=sponsor.id).all()
    return render_template('sponsor_dashboard.html', user = current_user, sponsor=sponsor, campaigns=campaigns,current_date=current_date, new_nego=new_nego)

@views.route('sponsor/profile',  methods=['GET', 'POST'])
@login_required
def sponsor_profile():
    sponsor = Sponsor.query.get(current_user.id)
    if request.method == 'POST':
        flag = True
        sponsor.name = request.form['name']
        sponsor.industry = request.form['industry']
        if request.form['budget']:
            sponsor.budget = float(request.form['budget'])
        db.session.commit()
        
        current_password = request.form.get('current_password')
        if current_password != "":
            new_password = request.form.get('new_password')
            if check_password_hash(current_user.password, current_password):
                current_user.password = generate_password_hash(new_password)
                db.session.commit()
            else:
                flash('Incorrect password', category='error')
                flag = False
        if flag:
            flash('Profile Updated', category='success')
            return render_template('sponsor_profile.html', user = current_user, sponsor = sponsor)
    return render_template('sponsor_profile.html', sponsor=sponsor, user = current_user)

@views.route('sponsor/campaigns',  methods=['GET', 'POST'])
@login_required
def sponsor_campaigns():
    sponsor = Sponsor.query.get(current_user.id)
    query = Campaign.query
    query = query.filter( Campaign.sponsor_id == sponsor.id)
    running_camp = query.filter( Campaign.end_date > datetime.now().date())
    noflag_campaigns = running_camp.filter_by( flagged = 'False').all()
    flag_campaigns = running_camp.filter_by( flagged = 'True').all()

    if request.method == 'POST':
        campaign_name_filter = request.form.get('campaign_filter')
        if campaign_name_filter:
            noflag_campaigns = [campaign for campaign in noflag_campaigns if campaign_name_filter.lower() in campaign.name.lower()]
            flag_campaigns = [campaign for campaign in flag_campaigns if campaign_name_filter.lower() in campaign.name.lower()]
            return render_template('campaigns.html', user=current_user, noflag_campaigns=noflag_campaigns, flag_campaigns=flag_campaigns)
        else:
            return render_template('campaigns.html', user=current_user, noflag_campaigns=noflag_campaigns, flag_campaigns=flag_campaigns)
            
    return render_template('campaigns.html', user=current_user, noflag_campaigns=noflag_campaigns, flag_campaigns=flag_campaigns)

@views.route('create_campaign', methods=['POST'])
def create_campaign():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description')
        startDate_str = request.form.get('startDate')
        endDate_str = request.form.get('endDate')
        budget = request.form.get('budget')
        visibility = request.form.get('visibility')
        
        start_date = datetime.strptime(startDate_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(endDate_str, '%Y-%m-%d').date()
        
        new_campaign = Campaign(name=name, description=description, start_date=start_date, end_date=end_date, budget=budget, visibility=visibility,flagged='False', sponsor_id=current_user.id)
        db.session.add(new_campaign)
        db.session.commit()

        flash('Campaign created successfully', category='success')
        return redirect(url_for('views.sponsor_campaigns'))
    
@views.route('/campaign/<int:campaign_id>', methods=['GET','POST'])
@login_required
def campaign_details(campaign_id):
    # Deleting previous negotiation if any
    query = Negotiation.query
    query = query.filter_by(sponsor_id = current_user.sponsor.id)
    query = query.filter(Negotiation.message == 'sponsor_accepted')
    negos = query.all()
    for nego in negos:
        db.session.delete(nego)
    db.session.commit()
    
    campaign = Campaign.query.filter_by(id=campaign_id).first()
    if request.method == 'POST':
        if request.form['action'] == 'update':
            start_date_str = request.form.get('start_date',campaign.start_date)
            end_date_str = request.form.get('end_date', campaign.end_date)
            
            campaign.name = request.form.get('name')
            campaign.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            campaign.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            campaign.budget = float(request.form.get('budget'))
            campaign.visibility = request.form.get('visibility')
            campaign.description = request.form.get('description',campaign.description)

            db.session.commit()
            
            flash('Profile Updated', category='success')
            return redirect(url_for('views.campaign_details', campaign_id=campaign.id))
        
        elif request.form['action'] == 'delete':
            campaign = Campaign.query.get(campaign_id)
            ad_requests = AdRequest.query.filter_by(campaign_id=campaign_id).all()
            for ad_request in ad_requests:
                negotiations = Negotiation.query.filter_by(ad_request_id=ad_request.id).all()
                for negotiation in negotiations:
                    db.session.delete(negotiation)
                db.session.delete(ad_request)

            db.session.delete(campaign)
            db.session.commit()
        
            flash('Campaign deleted successfully',category='success')
            return redirect(url_for('views.sponsor_campaigns'))
    
       
    return render_template('campaign_details.html', user=current_user, campaign=campaign)

@views.route('sponsor/stats')
@login_required
def sponsor_stats():
    sponsor = Sponsor.query.get(current_user.id)
    bar_data = [0,0,0]
    for camp in sponsor.campaigns:
        if camp.start_date > datetime.now().date():
            bar_data[0] += 1
        elif camp.start_date <= datetime.now().date() and camp.end_date >= datetime.now().date():
            bar_data[1] += 1
        else:
            bar_data[2] += 1

    return render_template('sponsor_stats.html', user=current_user, sponsor = sponsor, bar_data=bar_data, today_date= datetime.now().date())



@views.route('sponsor/decisions/<int:negotiation_id>', methods=['GET', 'POST'])
@login_required
def sponsor_decisions(negotiation_id):
    negotiation = Negotiation.query.filter_by(id=negotiation_id).first()
    campaign_id = negotiation.ad_request.campaign.id
    if request.method == 'POST':
        form_id = request.form.get('form_id')
        if form_id == 'new_request':
            action = request.form.get('action')
            if action == 'accept':
                if negotiation.sponsor.total_spent:
                    negotiation.sponsor.total_spent += negotiation.proposed_amount
                else:
                    negotiation.sponsor.total_spent = negotiation.proposed_amount
                
                if negotiation.influencer.earning:
                    negotiation.influencer.earning += negotiation.proposed_amount
                else:
                    negotiation.influencer.earning = negotiation.proposed_amount
                    
                negotiation.sponsor.total_spent += negotiation.ad_request.payment_amount
                negotiation.influencer.earning += negotiation.ad_request.payment_amount
                negotiation.ad_request.influencer_id = negotiation.influencer_id
                negotiation.ad_request.status = 'Accepted'
                negotiation.message = 'sponsor_accepted'    
                db.session.commit()  
                          
            elif action == 'reject':
                db.session.delete(negotiation)
                db.session.commit()
                
            else:
                amount = request.form.get('negotiation')
                negotiation.previous_time = negotiation.latest_time
                negotiation.latest_time = datetime.now()
                negotiation.proposed_amount = amount
                negotiation.message = 'sponsor_negotiated'
                db.session.commit()
        return redirect(url_for('views.campaign_details',campaign_id = campaign_id))
    
    
@views.route('/sponsor/update_delete/<int:adrequest_id>',methods=['POST','GET'])
@login_required
def update_delete(adrequest_id):
    ad_request = AdRequest.query.filter_by(id=adrequest_id).first()
    campaign_id = ad_request.campaign_id
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update':
            req = request.form.get('requirements',ad_request.requirements)
            amount = request.form.get('amount',ad_request.payment_amount)
            ad_request.requirements = req
            ad_request.payment_amount = amount
            db.session.commit()
            flash('Ad Request updated', category='success')
        if action == 'delete':
            for nego in ad_request.negotiations:
                db.session.delete(nego)
            db.session.delete(ad_request)
            db.session.commit()
            flash('Ad Request deleted', category='success')
            
        return redirect(url_for('views.campaign_details',campaign_id = campaign_id))
            
                

### END SPONSOR ROUTES ###

@views.route('campaign/<int:campaign_id>/createRequest', methods=['GET','POST'])
def create_adrequest(campaign_id):
    if request.method == 'POST':
        requirements = request.form.get('requirements')
        payment_amount = int(request.form.get('amount'))
        
        adrequest = AdRequest(campaign_id=campaign_id, requirements=requirements,payment_amount=payment_amount,status='Pending')
        db.session.add(adrequest)
        db.session.commit()
        return redirect(url_for('views.find_influencer',adrequest_id=adrequest.id))

@views.route('campaign/findInfluencer/<int:adrequest_id>', methods=['GET','POST'])
@login_required
def find_influencer(adrequest_id):
    if request.method == 'POST':
        name = request.form.get('name')
        reach = request.form.get('reach')
        niche = request.form.get('niche')
      
        query = Influencer.query
        if name:
            query = query.filter(Influencer.name.ilike(f'%{name}%'))
       
        if reach:
            try:
                min_reach, max_reach = map(int, reach.split('-'))
                query = query.filter(Influencer.reach.between(min_reach, max_reach))
            except ValueError:
                flash('Invalid reach filter',category='error')
  
        if niche and niche != "Niche":
            query = query.filter_by(niche=niche)

        influencers = query.all()
    
        return render_template('find_influencer.html',user=current_user,influencers=influencers,adrequest_id=adrequest_id)
        
    influencers = Influencer.query.order_by(Influencer.reach.desc()).limit(10).all()
    flash('Find an influencer',category='success')
    return render_template('find_influencer.html',user=current_user,influencers=influencers,adrequest_id=adrequest_id)
        

@views.route('sponsor/send_request/<int:influencer_id>/<int:adrequest_id>')
@login_required
def sponsor_send_request(influencer_id,adrequest_id):
    # Deleting previous negotiation if any
    prev_nego = Negotiation.query.filter_by(ad_request_id=adrequest_id).first()
    print(prev_nego)
    if prev_nego:
        db.session.delete(prev_nego)
        db.session.commit()
        
    adrequest = AdRequest.query.filter_by(id=adrequest_id).first()
    campaign = Campaign.query.filter_by(id=adrequest.campaign_id).first()
    sponsor = Sponsor.query.filter_by(id=campaign.sponsor_id).first()
    nego = Negotiation(ad_request_id=adrequest_id,sponsor_id=sponsor.id,influencer_id=influencer_id,proposed_amount=adrequest.payment_amount, latest_time = datetime.now(),message='sponsor_new')
    db.session.add(nego)
    db.session.commit()
    flash('Request sent', category='success')
    return redirect(url_for('views.campaign_details',campaign_id=campaign.id))


### INFLUENCER ROUTES ###
@views.route('influencer/dashboard')
@login_required
def influencer_dashboard():
    influencer = Influencer.query.get(current_user.id)
    negotiations = Negotiation.query.filter_by(influencer_id=influencer.id).all()

    return render_template('influencer_dashboard.html', user = current_user, influencer=influencer, current_date=datetime.now().date(), negotiations=negotiations)


@views.route('influencer/profile',  methods=['GET', 'POST'])
@login_required
def influencer_profile():
    influencer = Influencer.query.get(current_user.id)
    if request.method == 'POST':
        flag = True
        influencer.name = request.form['name']
        influencer.category = request.form['category']
        influencer.niche = request.form['niche']
        influencer.reach = int(request.form['reach'])
        
        current_password = request.form.get('current_password')
        if current_password != "":
            new_password = request.form.get('new_password')
            if check_password_hash(current_user.password, current_password):
                current_user.password = generate_password_hash(new_password)
                db.session.commit()
            else:
                flash('Incorrect password', category='error')
                flag = False
        if flag:
            flash('Profile Updated', category='success')
            return render_template('influencer_profile.html', user = current_user, influencer=influencer)
    return render_template('influencer_profile.html', influencer=influencer, user = current_user)

@views.route('/influencer/campaigns')
@login_required
def influencer_campaigns():
    
    #Deleteing unused negotiations
    query = Negotiation.query
    query = query.filter_by(influencer_id = current_user.influencer.id)
    query = query.filter(Negotiation.message == 'sponsor_accepted')
    negos = query.all()
    for nego in negos:
        db.session.delete(nego)
    db.session.commit()    
    
    
    influencer = Influencer.query.get(current_user.id)
    new_nego = Negotiation.query.filter_by(influencer_id=influencer.id, message='sponsor_new').all()
    sent_requests = Negotiation.query.filter_by(influencer_id=influencer.id, message='influencer_new').all()
    influencer_nego = Negotiation.query.filter_by(influencer_id=influencer.id, message='influencer_negotiated').all()
    sponsor_nego = Negotiation.query.filter_by(influencer_id=influencer.id, message='sponsor_negotiated').all()
   
    return render_template('influencer_campaigns.html', user=current_user,influencer=influencer, new_nego=new_nego,sent_requests=sent_requests, influencer_nego=influencer_nego, sponsor_nego=sponsor_nego)

@views.route('/influencer/search_campaigns', methods=['GET','POST'])
@login_required
def search_campaigns():
    influencer = Influencer.query.get(current_user.id)
    if request.method == 'POST':
        name = request.form.get('name')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        query = Campaign.query
        query = query.filter_by(visibility='Public',flagged='False')
        query = query.filter(Campaign.end_date > datetime.now().date())
        query = query.filter(Campaign.ad_requests.any())
        if name:
            query = query.filter(Campaign.name.ilike(f'%{name}%'))
       
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Campaign.start_date > start_date)

        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Campaign.end_date < end_date)

        campaigns = query.all()

        return render_template('search_campaigns.html', user=current_user, campaigns=campaigns,influencer=influencer)
    
    query = Campaign.query
    query = query.filter_by(visibility='Public',flagged='False')
    query = query.filter(Campaign.end_date > datetime.now().date())
    query = query.filter(Campaign.ad_requests.any())
    campaigns = query.limit(10).all()    
    return render_template('search_campaigns.html', user=current_user, campaigns=campaigns,influencer=influencer)

@views.route('/influencer/send_request/<int:adrequest_id>',methods=['POST','GET'])
@login_required
def influencer_send_request(adrequest_id):
    if request.method == 'POST':
        amount = float(request.form.get('negotiation_amount'))
        influencer = Influencer.query.get(current_user.id)
        adrequest = AdRequest.query.get(adrequest_id)
        new_nego = Negotiation(ad_request_id = adrequest_id,
                            sponsor_id = adrequest.campaign.sponsor.id,
                            influencer_id = influencer.id,
                            proposed_amount = amount,
                            message = 'influencer_new',
                            latest_time = datetime.now()
                            )
        db.session.add(new_nego)
        db.session.commit()
        flash('Request sent',category='success')
        return redirect(url_for('views.search_campaigns'))

@views.route('/influencer/negotiate/<int:nego_id>',methods=['POST','GET'])
@login_required
def influencer_negotiate(nego_id):
    negotiation = Negotiation.query.get(nego_id)
    adrequest = AdRequest.query.get(negotiation.ad_request_id)
    influencer = Influencer.query.get(current_user.id)
    if request.method == 'POST':
        action = request.form['action']
        if action == 'accept':
            if negotiation.sponsor.total_spent:
                negotiation.sponsor.total_spent += negotiation.proposed_amount
            else:
                negotiation.sponsor.total_spent = negotiation.proposed_amount
                
            if influencer.earning:
                influencer.earning += negotiation.proposed_amount
            else:
                influencer.earning = negotiation.proposed_amount
                
            adrequest.influencer_id = influencer.id
            adrequest.status = 'Accepted'
            adrequest.payment_amount = negotiation.proposed_amount
            db.session.commit()
            
            db.session.delete(negotiation)
            db.session.commit()
            flash('Request Accepted',category='success')
        elif action == 'reject':
            db.session.delete(negotiation)
            db.session.commit()
            flash('Request Rejected',category='error')
        elif action == 'negotiate':
            negotiation_amount = float(request.form['negotiation'])
            negotiation.previous_time = negotiation.latest_time
            negotiation.latest_time = datetime.now()
            negotiation.proposed_amount = negotiation_amount
            negotiation.message = 'influencer_negotiated'
            db.session.commit()
            
        
        return redirect(url_for('views.influencer_campaigns'))    
    
@views.route('influencer/stats')
@login_required
def influencer_stats():
    influencer = Influencer.query.get(current_user.id)

    return render_template('influencer_stats.html', user=current_user, influencer = influencer, today_date= datetime.now().date())

    
### END SINFLUENCER ROUTES ###


### ADMIN ROUTES ###
@views.route('/admin_dashboard',methods=['POST','GET'])
@login_required
def admin_dashboard():
    highest = db.session.query(
    Campaign.id,
    Campaign.name,
    db.func.sum(AdRequest.payment_amount).label('total_payment')
    ).join(
    AdRequest, Campaign.id == AdRequest.campaign_id
    ).group_by(
    Campaign.id
    ).order_by(
    desc('total_payment')).limit(5).all()
    print()
    highest = [[camp.name,camp.total_payment] for camp in highest]
    highest_labels = [li[0] for li in highest]
    highest_data = [li[1] for li in highest]
    
    campaigns = Campaign.query.filter( Campaign.end_date > datetime.now().date()).all()
    sponsors = Sponsor.query.all()
    influencers = Influencer.query.all()
    adrequests = AdRequest.query.all()
    return render_template('admin_dashboard.html',user=current_user, campaigns = campaigns, sponsors = sponsors, influencers = influencers, adrequests = adrequests, highest_labels=highest_labels, highest_data=highest_data)

# @views.route('/admin_manage',methods=['POST','GET'])
# @login_required
# def admin_manage():
#     campaigns = Campaign.query.filter( Campaign.end_date > datetime.now().date()).all()
#     sponsors = Sponsor.query.all()
#     influencers = Influencer.query.all()
#     adrequests = AdRequest.query.all()   
#     return render_template('admin_manage.html', user=current_user,  campaigns = campaigns, sponsors = sponsors, influencers = influencers, adrequests = adrequests)

@views.route('/admin/view_sponsors',methods=['GET','POST'])
@login_required
def view_sponsors():
    sponsor = Sponsor.query.get(id)
    sponsor.flagged = 'True'
    db.session.commit()
    
@views.route('/admin/view_influencers',methods=['GET','POST'])
@login_required
def view_influencers():
    sponsor = Sponsor.query.get(id)
    sponsor.flagged = 'True'
    db.session.commit()
    
@views.route('/admin/view_campaigns',methods=['GET','POST'])
@login_required
def view_campaigns():
    if request.method == 'POST':
        name = request.form.get('name')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        flagged = request.form.get('flagged')
        
        query = Campaign.query
        query = query.filter(Campaign.end_date > datetime.now().date())
        
        if name:
            query = query.filter(Campaign.name.ilike(f'%{name}%'))
       
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Campaign.start_date > start_date)

        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Campaign.end_date < end_date)
            
        if flagged:
            query = query.filter(Campaign.flagged == flagged)

        campaigns = query.all()
        return render_template('view_campaigns.html', user=current_user, campaigns=campaigns)
        
    campaigns = Campaign.query.filter(Campaign.end_date > datetime.now().date()).all()
    return render_template('view_campaigns.html', user=current_user, campaigns=campaigns)
    
@views.route('/admin/flag/<string:type>/<int:id>', methods=['POST'])
@login_required
def flag(type,id):
    if type == 'campaign':
        campaign = Campaign.query.get(id)
        campaign.flagged = 'True'
        db.session.commit()
    elif type == 'influencer':
        influencer = Influencer.query.get(id)
        influencer.user.flagged = 'True'
        db.session.commit()
    elif type == 'sponsor':
        sponsor = Sponsor.query.get(id)
        sponsor.user.flagged = 'True'
        db.session.commit()
    return redirect(url_for('views.view_campaigns'))

@views.route('/admin/unflag/<string:type>/<int:id>', methods=['POST'])
@login_required
def unflag(type,id):
    if type == 'campaign':
        campaign = Campaign.query.get(id)
        campaign.flagged = 'False'
        db.session.commit()
    elif type == 'influencer':
        influencer = Influencer.query.get(id)
        influencer.user.flagged = 'False'
        db.session.commit()
    elif type == 'sponsor':
        sponsor = Sponsor.query.get(id)
        sponsor.user.flagged = 'False'
        db.session.commit()
    return redirect(url_for('views.view_campaigns'))

### END ADMIN ROUTES ###

