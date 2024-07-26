from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    flagged = db.Column(db.String(5), nullable=True)

    # Relationships
    sponsor = db.relationship('Sponsor', back_populates='user', uselist=False)
    influencer = db.relationship('Influencer', back_populates='user', uselist=False)

class Sponsor(db.Model):
    __tablename__ = 'sponsor'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    industry = db.Column(db.String(100), nullable=False)
    budget = db.Column(db.Float, nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='sponsor')
    campaigns = db.relationship('Campaign', back_populates='sponsor')
    negotiations = db.relationship('Negotiation', back_populates='sponsor')

class Influencer(db.Model):
    __tablename__ = 'influencer'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    name = db.Column(db.String, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    niche = db.Column(db.String(100), nullable=False)
    reach = db.Column(db.Integer, nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='influencer')
    ad_requests = db.relationship('AdRequest', back_populates='influencer')
    negotiations = db.relationship('Negotiation', back_populates='influencer')

class Campaign(db.Model):
    __tablename__ = 'campaign'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    visibility = db.Column(db.String(50), nullable=False)
    flagged = db.Column(db.String(5),nullable=False)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))

    # Relationships
    sponsor = db.relationship('Sponsor', back_populates='campaigns')
    ad_requests = db.relationship('AdRequest', back_populates='campaign')

class AdRequest(db.Model):
    __tablename__ = 'ad_request'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'),nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'),nullable=True)
    requirements = db.Column(db.Text, nullable=True)
    payment_amount = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), nullable=False)#Pending , Accepted, Completed

    # Relationships
    campaign = db.relationship('Campaign', back_populates='ad_requests')
    influencer = db.relationship('Influencer', back_populates='ad_requests')
    negotiations = db.relationship('Negotiation', back_populates='ad_request')

class Negotiation(db.Model):
    __tablename__ = 'negotiation'
    id = db.Column(db.Integer, primary_key=True)
    ad_request_id = db.Column(db.Integer, db.ForeignKey('ad_request.id'))
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'))
    proposed_amount = db.Column(db.Float, nullable=False)
    previous_time = db.Column(db.DateTime, nullable=True)
    message = db.Column(db.Text, nullable=True) # sponsor_new, influencer_new, sponsor_negotiated, influencer_negotiated
    latest_time = db.Column(db.DateTime, nullable=True)

    # Relationships
    ad_request = db.relationship('AdRequest', back_populates='negotiations')
    sponsor = db.relationship('Sponsor', back_populates='negotiations')
    influencer = db.relationship('Influencer', back_populates='negotiations')
