from flask import request
from flask_restful import Resource,Api,reqparse
from .models import *
from flask_login import current_user

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
    # def get(self, campaign_id):
    #     campaign = Campaign.query.get(campaign_id)
    #     if campaign is None:
    #         return {'error': 'Campaign not found'}, 404
    #     else:
            
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

        return 'Campaign created successfully!', 201

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

        return 'Campaign updated successfully!', 200

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

        return 'Campaign deleted successfully!', 200

api.add_resource(CampaignAPI, '/api/campaigns', '/api/campaigns/<int:campaign_id>', '/api/campaigns/create/<int:sponsor_id>')
