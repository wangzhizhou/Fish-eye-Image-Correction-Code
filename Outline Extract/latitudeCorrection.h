//Written by WangZhizhou in TianJin University for the small paper and the interest.
#pragma once

#include "globalInclude.h"

Mat latitudeCorrection(Mat imgOrg, Point2i center, int radius, double camerFieldAngle = PI , CorrectType type = Reverse );
Mat latitudeCorrection2(Mat imgOrg, Point2i center, int radius, distMapMode distMap = LATITUDE_LONGTITUDE, double camerFieldAngle = PI,
	camMode camProjMode = EQUIDISTANCE);
Mat latitudeCorrection3(Mat imgOrg, Point2i center, int radius, distMapMode distMap = LATITUDE_LONGTITUDE, double theta_left=0, double phi_up=0, double camerFieldAngle = PI,
	camMode camProjMode = EQUIDISTANCE);
double func(double l, double phi);
double getPhi(double l);


Mat latitudeCorrection4(Mat imgOrg, Point2i center, int radius, double w_longtitude,double w_latitude, distMapMode distMap = LATITUDE_LONGTITUDE, double theta_left = 0, double phi_up = 0, double camerFieldAngle = PI,
	camMode camProjMode = EQUIDISTANCE);
double func1(double l, double phi,double w);
double getPhi1(double l,double w);
double auxFunc(double w, double phi);

Mat latitudeCorrection5(Mat imgOrg, Point2i center, int radius, double w_longtitude, double w_latitude, distMapMode distMap = LATITUDE_LONGTITUDE, double theta_left = 0, double phi_up = 0, double camerFieldAngle = PI,
	camMode camProjMode = EQUIDISTANCE);
