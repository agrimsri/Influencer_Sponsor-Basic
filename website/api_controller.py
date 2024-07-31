from flask import request,jsonify
from flask_restful import Resource,Api,reqparse
from .models import *
from flask_login import current_user
from werkzeug.security import generate_password_hash

api = Api()

camp_args = reqparse.RequestParser()
camp_args.add_argument("name")
camp_args.add_argument("description")
camp_args.add_argument("start_date")
camp_args.add_argument("end_date")
camp_args.add_argument("budget")
camp_args.add_argument("visibility")
camp_args.add_argument("flagged")
camp_args.add_argument("sponsor_id")

class CampaignAPI(Resource):
    def get(self, campaign_id):
        campaign = Campaign.query.get(campaign_id)
        if campaign is None:
            return jsonify({'message': 'Campaign not found'}), 404
        else:
            return jsonify( {
            'id': campaign.id,
            'name': campaign.name,
            'description': campaign.description,
            'start_date': campaign.start_date.strftime('%Y-%m-%d'),
            'end_date': campaign.end_date.strftime('%Y-%m-%d'),
            'budget': campaign.budget,
            'visibility': campaign.visibility,
            'flagged': campaign.flagged,
            'sponsor_id': campaign.sponsor_id
        })
        
            
    def post(self,sponsor_id):
        data = camp_args.parse_args()

        new_campaign = Campaign(
            name=data['name'],
            description=data['description'],
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
            budget=data['budget'],
            visibility=data['visibility'],
            flagged="False",
            sponsor_id=sponsor_id
        )

        db.session.add(new_campaign)
        db.session.commit()

        return jsonify({'message': 'Campaign created successfully'})

    def put(self, campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        data = camp_args.parse_args()

        campaign.name = data['name']
        campaign.description = data['description']
        campaign.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        campaign.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        campaign.budget = data['budget']
        campaign.visibility = data['visibility']
        campaign.flagged = "False" 
        
        db.session.commit()
        return jsonify({'message': 'Campaign updated successfully!'})
        

    def delete(self, campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        ad_requests = AdRequest.query.filter_by(campaign_id=campaign_id).all()
        for ad_request in ad_requests:
            negotiations = Negotiation.query.filter_by(ad_request_id=ad_request.id).all()
            for negotiation in negotiations:
                db.session.delete(negotiation)
            db.session.delete(ad_request)

        db.session.delete(campaign)
        db.session.commit()

        return jsonify({'message': 'Campaign deleted successfully!'})


user_parser = reqparse.RequestParser()
user_parser.add_argument('email', type=str)
user_parser.add_argument('password', type=str)
user_parser.add_argument('role', type=str)
user_parser.add_argument('flagged', type=str)

class UserResource(Resource):
    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        return jsonify({
            'id': user.id,
            'email': user.email,
            'role': user.role,
            'flagged': user.flagged
        })
        
    def put(self, user_id):
        user = User.query.get_or_404(user_id)
        args = user_parser.parse_args()
        
        if args['email'] is not None:
            user.email = args['email']
        if args['password'] is not None:
            user.password = generate_password_hash(args['password'],method='pbkdf2:sha256')
        if args['role'] is not None: # admin, user or sponsor
            user.role = args['role']
        if args['flagged'] is not None: # True or False
            user.flagged = args['flagged']
            
        db.session.commit()
        return jsonify({'message': 'User updated successfully'})


sponsor_parser = reqparse.RequestParser()
sponsor_parser.add_argument('email', type=str)
sponsor_parser.add_argument('password', type=str)
sponsor_parser.add_argument('name', type=str)
sponsor_parser.add_argument('industry', type=str)
sponsor_parser.add_argument('budget', type=float)
sponsor_parser.add_argument('total_spent', type=float)

class SponsorResource(Resource):
    def get(self, sponsor_id):
        sponsor = Sponsor.query.get_or_404(sponsor_id)
        return jsonify({
            'id': sponsor.id,
            'name': sponsor.name,
            'industry': sponsor.industry,
            'budget': sponsor.budget,
            'total_spent': sponsor.total_spent
        })

    def post(self):
        args = sponsor_parser.parse_args()
        new_user = User(
            email=args['email'],
            password=generate_password_hash(args['password'],method='pbkdf2:sha256'),
            role='sponsor',
            flagged='False'
        )
        db.session.add(new_user)
        db.session.commit()

        new_sponsor = Sponsor(
            id=new_user.id,
            name=args['name'],
            industry=args['industry'],
            budget=args['budget'],
            total_spent=args.get('total_spent')
        )
        db.session.add(new_sponsor)
        db.session.commit()
        return jsonify({'message': 'Sponsor created successfully'})

    def put(self, sponsor_id):
        sponsor = Sponsor.query.get_or_404(sponsor_id)
        args = sponsor_parser.parse_args()
        if args['name'] is not None:
            sponsor.name = args['name']
        if args['industry'] is not None:
            sponsor.industry = args['industry']
        if args['budget'] is not None:
            sponsor.budget = args['budget']
        if args['total_spent'] is not None:
            sponsor.total_spent = args['total_spent']
        db.session.commit()
        return jsonify({'message': 'Sponsor updated successfully'})


influencer_parser = reqparse.RequestParser()
influencer_parser.add_argument('email', type=str)
influencer_parser.add_argument('password', type=str)
influencer_parser.add_argument('name', type=str)
influencer_parser.add_argument('category', type=str)
influencer_parser.add_argument('niche', type=str)
influencer_parser.add_argument('reach', type=int)
influencer_parser.add_argument('earning', type=float)

class InfluencerResource(Resource):
    def get(self, influencer_id):
        influencer = Influencer.query.get_or_404(influencer_id)
        return jsonify({
            'id': influencer.id,
            'name': influencer.name,
            'category': influencer.category,
            'niche': influencer.niche,
            'reach': influencer.reach,
            'earning': influencer.earning
        })

    def post(self):
        args = influencer_parser.parse_args()
        new_user = User(
            email=args['email'],
            password=generate_password_hash(args['password'],method='pbkdf2:sha256'),
            role='influencer',
            flagged='False'
        )
        db.session.add(new_user)
        db.session.commit()

        new_influencer = Influencer(
            id=new_user.id,
            name=args['name'],
            category=args['category'],
            niche=args['niche'],
            reach=args['reach'],
            earning=args.get('earning')
        )
        db.session.add(new_influencer)
        db.session.commit()
        return jsonify({'message': 'Influencer created successfully'})

    def put(self, influencer_id):
        influencer = Influencer.query.get_or_404(influencer_id)
        args = influencer_parser.parse_args()
        if args['name'] is not None:
            influencer.name = args['name']
        if args['category'] is not None:
            influencer.category = args['category']
        if args['niche'] is not None:
            influencer.niche = args['niche']
        if args['reach'] is not None:
            influencer.reach = args['reach']
        if args['earning'] is not None:
            influencer.earning = args['earning']
        db.session.commit()
        return jsonify({'message': 'Influencer updated successfully'})



# Register API resources
api.add_resource(CampaignAPI, '/api/campaigns/<int:campaign_id>', '/api/campaigns', '/api/campaigns/sponsor/<int:sponsor_id>')
api.add_resource(UserResource, '/api/users', '/api/users/<int:user_id>')
api.add_resource(SponsorResource, '/api/sponsors', '/api/sponsors/<int:sponsor_id>')
api.add_resource(InfluencerResource, '/api/influencers', '/api/influencers/<int:influencer_id>')
