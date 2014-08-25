#include "latitudeCorrection.h"

Mat latitudeCorrection(Mat imgOrg, Point2i center, int radius, CorrectType type)
{
	Mat retImg(Size(WIDTH, HEIGHT), CV_8UC3, Scalar(0, 0, 0));


#ifndef _VIEW_FIELD_
	double dx = PI / WIDTH;
#else
	double dx = CAMER_VIEW_FIELD / WIDTH;
#endif
	double dy = dx;

	//coordinate for latitude map
	double latitude;
	double longitude;

	//unity sphere coordinate 
	double x, y, z, r;

	//parameter cooradinate of sphere coordinate
	double Theta_sphere;
	double Phi_sphere;

	//polar cooradinate for fish-eye Image
	double p;
	double theta;

	//cartesian coordinate 
	double x_cart, y_cart;

	//Image cooradinate of imgOrg
	int u, v;

	//Image cooradinate of imgRet
	int u_latitude, v_latitude;

	//offset of imgRet
	double longitude_offset, latitude_offset;


	Mat_<Vec3b> _retImg = retImg;
	Mat_<Vec3b> _imgOrg = imgOrg;

	//according to the correct type to do the calibration
	switch (type)
	{
	case Forward:
		int left, top;
		left = center.x - radius;
		top = center.y - radius;
		for (int j = top; j < top + 2 * radius; j++)
		{
			for (int i = left; i < left + 2 * radius; i++)
			{
				if (pow(i - center.x, 2) + pow(j - center.y, 2)>pow(radius, 2))
					continue;
				//Origin image cooradinate in pixel
				u = i;
				v = j;

				//Convert to cartiesian cooradinate in unity circle
				x_cart = (u - center.x) / (double)radius;
				y_cart = -(v - center.y) / (double)radius;

				//convert to polar axes
				theta = cvFastArctan(y_cart, x_cart)*PI / 180;
				p = sqrt(pow(x_cart, 2) + pow(y_cart, 2));

				//convert to sphere surface parameter cooradinate
				//Theta_sphere = p*CAMER_VIEW_FIELD / 2;
				Theta_sphere = PI / 2 - acos(p);
				Phi_sphere = theta;

				//convert to sphere surface 3D cooradinate
				x = sin(Theta_sphere)*cos(Phi_sphere);
				y = sin(Theta_sphere)*sin(Phi_sphere);
				z = cos(Theta_sphere);

				//convert to latitiude  cooradinate
				latitude = acos(y);
				longitude = cvFastArctan(z, -x)*PI / 180;

				//transform the latitude to pixel cooradinate
				u_latitude = (longitude / dx);
				v_latitude = (latitude / dy);

				//perform the map from the origin image to the latitude map image
				_retImg(v_latitude, u_latitude)[0] = _imgOrg(j, i)[0];
				_retImg(v_latitude, u_latitude)[1] = _imgOrg(j, i)[1];
				_retImg(v_latitude, u_latitude)[2] = _imgOrg(j, i)[2];
			}
		}

		break;
	case Reverse:

#ifdef _VIEW_FIELD_
		longitude_offset = (PI - CAMER_VIEW_FIELD) / 2;
 		latitude_offset = (PI - CAMER_VIEW_FIELD) / 2;
#endif

		for (int j = 0; j < HEIGHT; j++)
		{

#ifndef _VIEW_FIELD_
			latitude = j*dy;
#else
			latitude =latitude_offset+j*dy;
#endif

			for (int i = 0; i < WIDTH; i++)
			{
				
#ifndef _VIEW_FIELD_
				longitude = i*dx;
#else
				longitude = longitude_offset+i*dx;
#endif

				//Convert from latitude cooradinate to the sphere cooradinate
				x = -sin(latitude)*cos(longitude);
				y = cos(latitude);
				z = sin(latitude)*sin(longitude);

				//Convert from sphere cooradinate to the parameter sphere cooradinate
				Theta_sphere = acos(z);
				Phi_sphere = cvFastArctan(y, x);//return value in Angle
				Phi_sphere = Phi_sphere*PI / 180;//Convert from Angle to Radian

				//Convert from parameter sphere cooradinate to fish-eye polar cooradinate
				//p = 2 * Theta_sphere / CAMER_VIEW_FIELD;
				double R = radius / sin(CAMER_VIEW_FIELD / 2);

				p = sin(Theta_sphere);  
				theta = Phi_sphere;

				//Convert from fish-eye polar cooradinate to cartesian cooradinate
				x_cart = p*cos(theta);
				y_cart = p*sin(theta);

				//Convert from cartesian cooradinate to image cooradinate
				u = x_cart*R + center.x;
				v = -y_cart*R + center.y;

				if (pow(u - center.x, 2) + pow(v - center.y, 2)>pow(radius,2))
					continue;

				_retImg(j, i)[0] = _imgOrg(v, u)[0];
				_retImg(j, i)[1] = _imgOrg(v, u)[1];
				_retImg(j, i)[2] = _imgOrg(v, u)[2];
				
			}
		}

		break;
	default:
		cout << "The CorrectType is Wrong!" << endl;
		abort();
		//break;
	}

#ifdef _DEBUG_
	namedWindow("Corrected Image", CV_WINDOW_AUTOSIZE);
	imshow("Corrected Image", retImg );
	waitKey();
#endif
	return retImg;
}