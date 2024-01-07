#pragma once
#include "globalInclude.h"
#include "tools.h"
#include "findCircleParameter.h"

typedef struct correctParameters
{
	Mat imgOrg;
	Point2i center;
	int radius; 
	double w_longtitude; 
	double w_latitude; 
	distMapMode distMap ; 
	double theta_left ; 
	double phi_up ; 
	double camerFieldAngle ; 
	camMode camProjMode;
	CorrectType typeOfCorrect;
}correctParams;

class corrector
{
public:
	enum correctMethod
	{
		LONG_LAT_MAP_REVERSE_FORWARD,
		PERSPECTIVE_LONG_LAT_MAP_CAMERA_LEN_MODEL,
		PERSPECTIVE_LONG_LAT_MAP_CAMERA_LEN_MODEL_REVERSE_W_HALF_PI,
		PERSPECTIVE_LONG_LAT_MAP_CAMERA_LEN_MODEL_REVERSE_W_VARIABLE,
		PERSPECTIVE_LONG_LAT_MAP_CAMERA_LEN_MODEL_FORWORD_W_VARIABLE
	};

public:
	corrector(){}
	~corrector(){};
	static void dispHeaveAndEarthCorrectImage(Mat sourceImage);
	Mat correctImage(correctParameters params, correctMethod method, bool isDispRet);
private:
	static Mat heavenAndEarthCorrect(Mat imgOrg, Point center, int radius, double startRadian = 0, CorrectType type = Reverse);
	
private:

#pragma region 鱼眼图像校正部分成员函数
	 Mat latitudeCorrection(Mat imgOrg, Point2i center, int radius, double camerFieldAngle = PI, CorrectType type = Reverse);
	 Mat latitudeCorrection2(Mat imgOrg, Point2i center, int radius, distMapMode distMap = LATITUDE_LONGTITUDE, double camerFieldAngle = PI, camMode camProjMode = EQUIDISTANCE);
	 Mat latitudeCorrection3(Mat imgOrg, Point2i center, int radius, distMapMode distMap = LATITUDE_LONGTITUDE, double theta_left = 0, double phi_up = 0, double camerFieldAngle = PI, camMode camProjMode = EQUIDISTANCE);
	 static double func(double l, double phi);
	 static double getPhi(double l);

	 Mat latitudeCorrection4(Mat imgOrg, Point2i center, int radius, double w_longtitude, double w_latitude, distMapMode distMap = LATITUDE_LONGTITUDE, double theta_left = 0, double phi_up = 0, double camerFieldAngle = PI, camMode camProjMode = EQUIDISTANCE);

	 static double func1(double l, double phi, double w);
	 static double getPhi1(double l, double w);
	 static double auxFunc(double w, double phi);

	 Mat latitudeCorrection5(Mat imgOrg, Point2i center, int radius, double w_longtitude, double w_latitude, distMapMode distMap = LATITUDE_LONGTITUDE, double theta_left = 0, double phi_up = 0, double camerFieldAngle = PI, camMode camProjMode = EQUIDISTANCE);
#pragma endregion
private:
	static int counter;
};