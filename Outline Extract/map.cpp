#include "map.h"

void findPoints(Point2i center, int radius,std::vector<cv::Point> &points, camMode projMode)
{
	std::vector<cv::Point3f> spherePoints(points.size());
	std::vector<cv::Point3f>::iterator itSphere = spherePoints.begin();
	
	cout << points << endl;
	
	std::vector<cv::Point>::iterator it = points.begin();

	while (it != points.end())
	{
		int u = it->x;
		int v = it->y;

		//Convert to cartiesian cooradinate in unity circle
		int x_cart = (u - center.x);
		int y_cart = -(v - center.y);

		//convert to polar axes
		double theta = cvFastArctan(y_cart, x_cart)*PI / 180;
		double p = sqrt(pow(x_cart, 2) + pow(y_cart, 2));


		double foval = 0.0;
		double Theta_sphere;
		switch (projMode)
		{

		case STEREOGRAPHIC:
			foval = radius / (2 * tan(FOV / 4));
			Theta_sphere = 2 * atan(p / (2 * foval));
			break;
		case EQUIDISTANCE:
			foval = radius / (FOV / 2);
			Theta_sphere = p / foval;
			break;
		case EQUISOLID:
			foval = radius / (2 * sin(FOV / 4));
			Theta_sphere = 2 * asin(p / (2 * foval));
			break;
		case ORTHOGONAL:
			foval = radius / sin(FOV / 2);
			Theta_sphere = asin(p / foval);
			break;
		default:
			cout << "The camera mode hasn't been choose!" << endl;
		}

		//convert to sphere surface parameter cooradinate
		double Phi_sphere = theta;

		//convert to sphere surface 3D cooradinate
		itSphere->x = sin(Theta_sphere)*cos(Phi_sphere);
		itSphere->y = sin(Theta_sphere)*sin(Phi_sphere);
		itSphere->z = cos(Theta_sphere);
		
		double temp = itSphere->x*itSphere->x +
			itSphere->y*itSphere->y +
			itSphere->z*itSphere->z;
		cout << "[x, y, z] = "<<*itSphere<<endl
			<<"norm = "<<sqrt(temp) << endl;

		++it;
		++itSphere;
	}
///////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////
	double angle = acos(spherePoints[0].dot(spherePoints[1]));

	//double angle = PI;
	cout << "spherePoints[0]=" << spherePoints[0] << endl;
	cout << "spherePoints[1]=" << spherePoints[1] << endl;

	cv::Point3f e3 = spherePoints[0].cross(spherePoints[1]);
	double norm_e3 = norm(e3);
	e3.x /= norm_e3;
	e3.y /= norm_e3;
	e3.z /= norm_e3;

	if (e3.dot(Point3f(0, 0, 1)) < 0)
	{
		e3 = spherePoints[1].cross(spherePoints[0]);
		double norm_e3 = norm(e3);
		e3.x /= norm_e3;
		e3.y /= norm_e3;
		e3.z /= norm_e3;

		//swap shpereSpoint[0] and spherePoints[1]
		spherePoints[0] = spherePoints[0] + spherePoints[1];
		spherePoints[1] = spherePoints[0] - spherePoints[1];
		spherePoints[0] = spherePoints[0] - spherePoints[1];
		
	}
	cv::Point3f e1 = spherePoints[0];
	cv::Point3f e2 = e3.cross(e1);

	cout << "e1.e2=" << e1.dot(e2) << endl
		<< e2.dot(e3) << endl
		<< e3.dot(e1) << endl;
	cout << "norm(e1)=" << norm(e1) << endl << norm(e2) << endl
		<< norm(e3) << endl;
	std::vector<Point3f> tmpK;
	tmpK.push_back(e1);
	tmpK.push_back(e2);	
	tmpK.push_back(e3);
	cout << e1 << endl << e2 << endl << e3 << endl;
	cout << "tmpK=" << tmpK << endl;
	Mat K = Mat(tmpK).reshape(1).t(); //从标准空间坐标到报像头空间坐标的变换矩阵
	cout << "K=" << K << endl;
	Mat T = K.inv(CV_SVD);//从报像头空间坐标到标准空间坐标平面变换矩阵
	
	points.clear();
	const int count = 20;
	double step = angle / count;
	double start = 0.0;
	int l = 0;
	while (l++<=count)
	{
		Point3f stdPt(cos(start), sin(start), 0);
		Mat  matPt(stdPt);
	
		cout << matPt << endl << K << endl;
		Mat ptSphere(K*matPt);
		cout << ptSphere << endl;
		Mat_<double> ptSphere_double;
		ptSphere.convertTo(ptSphere_double, CV_64F);
		double x = ptSphere_double.at<double>(0, 0);
		double y = ptSphere_double.at<double>(1, 0);
		double z = ptSphere_double.at<double>(2, 0);

		cout << x << ", " << y << ", " << z << endl;

		//Convert from sphere cooradinate to the parameter sphere cooradinate
		double Theta_sphere = acos(z);
		double Phi_sphere = cvFastArctan(y, x)*PI / 180;//return value in Angle
////////////////////////////////////////////////////////////////////////////////

		double foval = 0.0;
		double p;
		switch (projMode)
		{                                                                                    

		case STEREOGRAPHIC:
			foval = radius / (2 * tan(FOV / 4));
			p = 2 * foval*tan(Theta_sphere / 2);
			break;
		case EQUIDISTANCE:
			foval = radius / (FOV / 2);
			p = foval*Theta_sphere;
			break;
		case EQUISOLID:
			foval = radius / (2 * sin(FOV / 4));
			p = 2 * foval*sin(Theta_sphere / 2);
			break;
		case ORTHOGONAL:
			foval = radius / sin(FOV / 2);
			p = foval*sin(Theta_sphere);
			break;
		default:
			cout << "The camera mode hasn't been choose!" << endl;
		}
		//Convert from parameter sphere cooradinate to fish-eye polar cooradinate
		//p = sin(Theta_sphere);
		double theta = Phi_sphere;

		//Convert from fish-eye polar cooradinate to cartesian cooradinate
		double x_cart = p*cos(theta);
		double y_cart = p*sin(theta);

		//double R = radius / sin(camerFieldAngle / 2);

		//Convert from cartesian cooradinate to image cooradinate
		double u = x_cart + center.x;
		double v = -y_cart + center.y;

		Point pt = Point(u, v);
		points.push_back(pt);
//////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////
		start += step;
	}
/////////////////////////////////////////////////////////////////////
	cout << points << endl;
}