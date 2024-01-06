#include "corrector.h"


#pragma region 静态成员变量和函数
int corrector::counter = 0;

//以动态的方式显示被校正的图像
void corrector::dispHeaveAndEarthCorrectImage(Mat sourceImage)
{
	Mat image = sourceImage.clone();
	Point2i center;
	int radius;

	Mat dispImage;

	string win_name = "Heaven And Earth Correct";
	cv::namedWindow(win_name, CV_WINDOW_NORMAL | CV_WINDOW_KEEPRATIO);

	if (findCircleParameter::getCircleParatemer(center, radius) && image.data)
	{
		for (double r = PI / 20; r <= PI; r += PI / 20)
		{
			dispImage = heavenAndEarthCorrect(image.clone(), center, radius, r, Reverse);
			if (dispImage.data)
			{
				imshow(win_name, dispImage);
				cv::waitKey(10);
			}
		}
		cv::waitKey();
		cv::destroyWindow(win_name);
	}
}

//对于向天和向地拍摄的鱼眼图片校正
Mat corrector::heavenAndEarthCorrect(Mat imgOrg, Point center, int radius, double startRadian, CorrectType type)
{
	//设定展开图的高度，因为鱼眼图像不能灰复高度信息，所以这里可以跟根实际来
	//进行调节
	int heightOfPanorama = radius * 2;

	//设定展开图的宽度，这里设定为鱼眼图像圆形有效区域的周长
	int widthOfPanorama = 2 * PI*radius;

	double dx = 2 * PI / widthOfPanorama;
	double dy = radius / (double)heightOfPanorama;

	double p;
	double theta;

	double x, y;

	int u, v;

	//展开图的变量分配
	Mat retImg(heightOfPanorama, widthOfPanorama, CV_8UC3, Scalar(0, 0, 0));
	cv::Mat_<Vec3b> _retImg = retImg;
	cv::Mat_<Vec3b> _imgOrg = imgOrg.clone();

	switch (type)
	{
	case Reverse:	//使用反向映射来填充展开图
		for (int j = 0; j < heightOfPanorama; j++)
		{
			for (int i = 0; i < widthOfPanorama; i++)
			{
				p = j*dy;
				theta = i*dx + startRadian;

				x = p*cos(theta);
				y = p*sin(theta);

				u = x + center.x;
				v = y + center.y;

				_retImg(j, i)[0] = _imgOrg(v, u)[0];
				_retImg(j, i)[1] = _imgOrg(v, u)[1];
				_retImg(j, i)[2] = _imgOrg(v, u)[2];

			}
		}
		break;

	case Forward:
		int left, top;
		left = center.x - radius;
		top = center.y - radius;
		for (int j = top; j < top + 2 * radius; j++)
		{
			for (int i = left; i < left + 2 * radius; i++)
			{
				if (pow(i - center.x, 2) + pow(j - center.y, 2) > pow(radius, 2))
					continue;

				u = i;
				v = j;

				x = (u - center.x);
				y = -(v - center.y);

				//convert to polar axes
				theta = cvFastArctan(y, x)*PI / 180;
				p = sqrt(pow(x, 2) + pow(y, 2));

				theta -= startRadian;
				theta = theta < 0 ? theta + 2 * PI : theta;

				int u_ret = theta / dx;
				int v_ret = p / dy;

				if (u_ret < 0 || u_ret >= widthOfPanorama || v_ret < 0 || v_ret >= heightOfPanorama)
					continue;

				//perform the map from the origin image to the latitude map image
				_retImg(v_ret, u_ret)[0] = _imgOrg(j, i)[0];
				_retImg(v_ret, u_ret)[1] = _imgOrg(j, i)[1];
				_retImg(v_ret, u_ret)[2] = _imgOrg(j, i)[2];
			}
		}

		break;
	}

#ifdef _DEBUG_
	cv::namedWindow("expand fish-eye image", CV_WINDOW_AUTOSIZE);
	imshow("expand fish-eye image", retImg);
	cv::waitKey();
#endif
	return	retImg;
}

#pragma endregion

Mat corrector::correctImage(correctParameters params, correctMethod method,bool isDispRet)
{
	Mat resultImage;
	switch (method)
	{
	case correctMethod::LONG_LAT_MAP_REVERSE_FORWARD:
		resultImage = latitudeCorrection(params.imgOrg, params.center, params.radius, params.camerFieldAngle, params.typeOfCorrect);
		break;
	case correctMethod::PERSPECTIVE_LONG_LAT_MAP_CAMERA_LEN_MODEL:
		resultImage = latitudeCorrection2(params.imgOrg, params.center, params.radius, params.distMap, params.camerFieldAngle, params.camProjMode);
		break;
	case correctMethod::PERSPECTIVE_LONG_LAT_MAP_CAMERA_LEN_MODEL_REVERSE_W_HALF_PI:
		resultImage = latitudeCorrection3(params.imgOrg, params.center, params.radius, params.distMap, params.theta_left, params.phi_up, params.camerFieldAngle, params.camProjMode);
		break;
	case correctMethod::PERSPECTIVE_LONG_LAT_MAP_CAMERA_LEN_MODEL_REVERSE_W_VARIABLE:
		resultImage = latitudeCorrection4(params.imgOrg, params.center, params.radius, params.w_longtitude, params.w_latitude, params.distMap, params.theta_left, params.phi_up, params.camerFieldAngle, params.camProjMode);
		break;
	case correctMethod::PERSPECTIVE_LONG_LAT_MAP_CAMERA_LEN_MODEL_FORWORD_W_VARIABLE:
		resultImage = latitudeCorrection5(params.imgOrg, params.center, params.radius, params.w_longtitude, params.w_latitude, params.distMap, params.theta_left, params.phi_up, params.camerFieldAngle, params.camProjMode);
		break;
	default:
		cout << "You had not choose a method to correct the image!" << endl;
	}

	counter++;

	cout << "Image " << counter << " corrected!" << endl;
	if (isDispRet)
	{
		string win_name("The result Image"+to_string(counter));

		Mat resizedImage;
		resize(params.imgOrg, resizedImage, Size((params.imgOrg.size().width / (double)params.imgOrg.size().height*resultImage.size().height), resultImage.size().height));

		Mat compareTwoImages(Size(resizedImage.size().width + 10 + resultImage.size().width, resultImage.size().height), resultImage.type());
		Rect sourceROI(0, 0, resizedImage.size().width, resizedImage.size().height);
		Rect resultROI(resizedImage.size().width + 10, 0, resultImage.size().width, resultImage.size().height);

		Mat sourceTemp = compareTwoImages(sourceROI);
		Mat resultTemp = compareTwoImages(resultROI);

		addWeighted(sourceTemp, 0, resizedImage, 1, 0, sourceTemp);
		addWeighted(resultTemp, 0, resultImage, 1, 0, resultTemp);

		cv::namedWindow(win_name, CV_WINDOW_NORMAL | CV_WINDOW_KEEPRATIO);
		cv::resizeWindow(win_name, compareTwoImages.size().width / (double)compareTwoImages.size().height * 512, 512);
		imshow(win_name, compareTwoImages);
		cv::waitKey();
		cv::destroyWindow(win_name);
	}
	return resultImage;
}

#pragma region 关于经纬度以及纵向压缩柱面投影校正的方法(动态成员)
//longitude-latitude reverse or forward map correction method
Mat corrector::latitudeCorrection(Mat imgOrg, Point2i center, int radius, double camerFieldAngle, CorrectType type)
{
	if (!(camerFieldAngle > 0 && camerFieldAngle <= PI))
	{
		cout << "The parameter \"camerFieldAngle\" must be in the interval (0,PI]." << endl;
		return Mat();
	}
	double rateOfWindow = 0.9;
	int width = imgOrg.size().width*rateOfWindow;
	int height = width;
	Size imgSize(width, height);

	Mat retImg(imgSize, CV_8UC3, Scalar(0, 0, 0));

	double dx = camerFieldAngle / imgSize.width;
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

	//offset of imgRet Origin
	double longitude_offset, latitude_offset;
	longitude_offset = (PI - camerFieldAngle) / 2;
	latitude_offset = (PI - camerFieldAngle) / 2;

	cv::Mat_<Vec3b> _retImg = retImg;
	cv::Mat_<Vec3b> _imgOrg = imgOrg;

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
				if (pow(i - center.x, 2) + pow(j - center.y, 2) > pow(radius, 2))
					continue;
				//Origin image cooradinate in pixel
				u = i;
				v = j;

				double R = radius / sin(camerFieldAngle / 2);

				//Convert to cartiesian cooradinate in unity circle
				x_cart = (u - center.x) / R;
				y_cart = -(v - center.y) / R;

				//convert to polar axes
				theta = cvFastArctan(y_cart, x_cart)*PI / 180;
				p = sqrt(pow(x_cart, 2) + pow(y_cart, 2));

				//convert to sphere surface parameter cooradinate
				Theta_sphere = asin(p);
				Phi_sphere = theta;

				//convert to sphere surface 3D cooradinate
				x = sin(Theta_sphere)*cos(Phi_sphere);
				y = sin(Theta_sphere)*sin(Phi_sphere);
				z = cos(Theta_sphere);

				//convert to latitiude  cooradinate
				latitude = acos(y);
				longitude = cvFastArctan(z, -x)*PI / 180;

				//transform the latitude to pixel cooradinate

				u_latitude = ((longitude - longitude_offset) / dx);
				v_latitude = ((latitude - latitude_offset) / dy);

				if (u_latitude < 0 || u_latitude >= imgSize.height || v_latitude < 0 || v_latitude >= imgSize.width)
					continue;

				//perform the map from the origin image to the latitude map image
				_retImg(v_latitude, u_latitude)[0] = _imgOrg(j, i)[0];
				_retImg(v_latitude, u_latitude)[1] = _imgOrg(j, i)[1];
				_retImg(v_latitude, u_latitude)[2] = _imgOrg(j, i)[2];
			}
		}

		break;

	case Reverse:

		for (int j = 0; j < imgSize.height; j++)
		{

			latitude = latitude_offset + j*dy;
			for (int i = 0; i < imgSize.width; i++)
			{

				longitude = longitude_offset + i*dx;
				//Convert from latitude cooradinate to the sphere cooradinate
				x = -sin(latitude)*cos(longitude);
				y = cos(latitude);
				z = sin(latitude)*sin(longitude);

				//Convert from sphere cooradinate to the parameter sphere cooradinate
				Theta_sphere = acos(z);
				Phi_sphere = cvFastArctan(y, x);//return value in Angle
				Phi_sphere = Phi_sphere*PI / 180;//Convert from Angle to Radian


				//Convert from parameter sphere cooradinate to fish-eye polar cooradinate
				p = sin(Theta_sphere);
				theta = Phi_sphere;

				//Convert from fish-eye polar cooradinate to cartesian cooradinate
				x_cart = p*cos(theta);
				y_cart = p*sin(theta);

				//double R = radius / sin(camerFieldAngle / 2);
				double R = radius;
				//Convert from cartesian cooradinate to image cooradinate
				u = x_cart*R + center.x;
				v = -y_cart*R + center.y;

				//if (pow(u - center.x, 2) + pow(v - center.y, 2) > pow(radius, 2))
				//{
				//	_imgOrg(v, u)[0] = 255;
				//	_imgOrg(v, u)[1] = 255;
				//	_imgOrg(v, u)[2] = 255;
				//	continue;
				//}

				_retImg.at<Vec3b>(j, i) = _imgOrg.at<Vec3b>(v, u);
			}
		}

		break;
	default:
		cout << "The CorrectType is Wrong! It should be \"Forward\" or \"Reverse\"." << endl;
		return Mat();
	}

	//imwrite("C:\\Users\\Joker\\Desktop\\ret4.jpg", retImg);
	//imshow("org", _imgOrg);
	//imshow("ret", _retImg);
	//cv::waitKey();
#ifdef _DEBUG_
	cv::namedWindow("Corrected Image", CV_WINDOW_AUTOSIZE);
	imshow("Corrected Image", retImg);
	cv::waitKey();
#endif
	return retImg;
}

//persective or longitude-latitude map with camera len model optional
Mat corrector::latitudeCorrection2(Mat imgOrg, Point2i center, int radius, distMapMode distMap, double camerFieldAngle, camMode camProjMode)
{
	if (!(camerFieldAngle > 0 && camerFieldAngle <= PI))
	{
		cout << "The parameter \"camerFieldAngle\" must be in the interval (0,PI]." << endl;
		return Mat();
	}
	double rateOfWindow = 0.9;
	//int width = imgOrg.size().width*rateOfWindow;
	//int height = width;

	int width = max(imgOrg.cols, imgOrg.rows);
	int height = width;


	Size imgSize(width, height);
	int center_x = imgSize.width / 2;
	int center_y = imgSize.height / 2;

	Mat retImg(imgSize, CV_8UC3, Scalar(0, 0, 0));

	double dx = camerFieldAngle / imgSize.width;
	double dy = camerFieldAngle / imgSize.height;

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
	double u, v;
	Point pt, pt1, pt2, pt3, pt4;

	//Image cooradinate of imgRet
	int u_latitude, v_latitude;
	Rect imgArea(0, 0, imgOrg.cols, imgOrg.rows);

	//offset of imgRet Origin
	double longitude_offset, latitude_offset;
	longitude_offset = (PI - camerFieldAngle) / 2;
	latitude_offset = (PI - camerFieldAngle) / 2;

	double foval = 0.0;//焦距


	cv::Mat_<Vec3b> _retImg = retImg;
	cv::Mat_<Vec3b> _imgOrg = imgOrg;

	//according to the camera type to do the calibration
	for (int j = 0; j < imgSize.height; j++)
	{

		for (int i = 0; i < imgSize.width; i++)
		{
			Point3f tmpPt(i - center_x, center_y - j, 100);//最后一个参数用来修改成像面的焦距
			double normPt = norm(tmpPt);

			switch (distMap)
			{
			case PERSPECTIVE:

				tmpPt.x /= normPt;
				tmpPt.y /= normPt;
				tmpPt.z /= normPt;
				x = tmpPt.x;
				y = tmpPt.y;
				z = tmpPt.z;

				break;
			case LATITUDE_LONGTITUDE:

				//latitude = latitude_offset + atan((double)j/(double)(imgSize.height-j));
				//longitude = longitude_offset + i*dx;

				latitude = latitude_offset + j*dy;
				longitude = longitude_offset + i*dx;
				//Convert from latitude cooradinate to the sphere cooradinate
				x = -sin(latitude)*cos(longitude);
				y = cos(latitude);
				z = sin(latitude)*sin(longitude);

				break;
			default:
				break;
			}

			//Convert from unit sphere cooradinate to the parameter sphere cooradinate
			Theta_sphere = acos(z);
			Phi_sphere = cvFastArctan(y, x);//return value in Angle
			Phi_sphere = Phi_sphere*PI / 180;//Convert from Angle to Radian


			switch (camProjMode)
			{
			case STEREOGRAPHIC:
				foval = radius / (2 * tan(camerFieldAngle / 4));
				p = 2 * foval*tan(Theta_sphere / 2);
				break;
			case EQUIDISTANCE:
				foval = radius / (camerFieldAngle / 2);
				p = foval*Theta_sphere;
				break;
			case EQUISOLID:
				foval = radius / (2 * sin(camerFieldAngle / 4));
				p = 2 * foval*sin(Theta_sphere / 2);
				break;
			case ORTHOGONAL:
				foval = radius / sin(camerFieldAngle / 2);
				p = foval*sin(Theta_sphere);
				break;
			default:
				cout << "The camera mode hasn't been choose!" << endl;
			}
			//Convert from parameter sphere cooradinate to fish-eye polar cooradinate
			//p = sin(Theta_sphere);
			theta = Phi_sphere;

			//Convert from fish-eye polar cooradinate to cartesian cooradinate
			x_cart = p*cos(theta);
			y_cart = p*sin(theta);

			//double R = radius / sin(camerFieldAngle / 2);

			//Convert from cartesian cooradinate to image cooradinate
			u = x_cart + center.x;
			v = -y_cart + center.y;

			pt = Point(u, v);

			if (!pt.inside(imgArea))
			{
				continue;
			}

			_retImg.at<Vec3b>(j, i) = _imgOrg.at<Vec3b>(pt);

		}
	}

	//imshow("org", _imgOrg);
	//imshow("ret", _retImg);
	//cv::waitKey();
#ifdef _DEBUG_
	cv::namedWindow("Corrected Image", CV_WINDOW_AUTOSIZE);
	imshow("Corrected Image", retImg);
	cv::waitKey();
#endif
	//imwrite("ret.jpg", retImg);
	return retImg;
}

//w=PI/2
Mat corrector::latitudeCorrection3(Mat imgOrg, Point2i center, int radius, distMapMode distMap, double theta_left, double phi_up, double camerFieldAngle, camMode camProjMode)
{
	if (!(camerFieldAngle > 0 && camerFieldAngle <= PI))
	{
		cout << "The parameter \"camerFieldAngle\" must be in the interval (0,PI]." << endl;
		return Mat();
	}
	double rateOfWindow = 0.9;

	//int width = imgOrg.size().width*rateOfWindow;
	//int height = width;

	int width = max(imgOrg.cols, imgOrg.rows);
	int height = width;
	//int height = imgOrg.rows;


	Size imgSize(width, height);
	int center_x = imgSize.width / 2;
	int center_y = imgSize.height / 2;

	Mat retImg(imgSize, CV_8UC3, Scalar(0, 0, 0));

	double dx = camerFieldAngle / imgSize.width;
	double dy = camerFieldAngle / imgSize.height;

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
	double u, v;
	Point pt, pt1, pt2, pt3, pt4;

	//Image cooradinate of imgRet
	int u_latitude, v_latitude;
	Rect imgArea(0, 0, imgOrg.cols, imgOrg.rows);

	//offset of imgRet Origin
	double longitude_offset, latitude_offset;
	longitude_offset = (PI - camerFieldAngle) / 2;
	latitude_offset = (PI - camerFieldAngle) / 2;

	double foval = 0.0;//焦距


	cv::Mat_<Vec3b> _retImg = retImg;
	cv::Mat_<Vec3b> _imgOrg = imgOrg;

	//according to the camera type to do the calibration
	for (int j = 0; j < imgSize.height; j++)
	{

		for (int i = 0; i < imgSize.width; i++)
		{
			Point3f tmpPt(i - center_x, center_y - j, 600);//最后一个参数用来修改成像面的焦距
			double normPt = norm(tmpPt);

			switch (distMap)
			{
			case PERSPECTIVE:

				tmpPt.x /= normPt;
				tmpPt.y /= normPt;
				tmpPt.z /= normPt;

				x = tmpPt.x;
				y = tmpPt.y;
				z = tmpPt.z;

				break;
			case LATITUDE_LONGTITUDE:

				//latitude = latitude_offset + j*dy;

				latitude = getPhi((double)j*4.0 / imgSize.height);

				longitude = getPhi((double)i * 4 / imgSize.width);

				//latitude = latitude_offset + j*dy;
				//longitude = longitude_offset + i*dx;
				//Convert from latitude cooradinate to the sphere cooradinate
				x = -sin(latitude)*cos(longitude);
				y = cos(latitude);
				z = sin(latitude)*sin(longitude);

				break;
			default:
				break;
			}

			if (distMap == PERSPECTIVE)
			{
				//double theta = PI/4;
				//double phi = -PI/2;
				cv::Mat curPt(cv::Point3f(x, y, z));
				std::vector<cv::Point3f> pts;

				//向东旋转地球
				//pts.push_back(cv::Point3f(cos(theta), 0, -sin(theta)));
				//pts.push_back(cv::Point3f(0, 1, 0));
				//pts.push_back(cv::Point3f(sin(theta), 0, cos(theta)));

				//向南旋转地球
				//pts.push_back(cv::Point3f(1, 0, 0));
				//pts.push_back(cv::Point3f(0, cos(phi), sin(phi)));
				//pts.push_back(cv::Point3f(0, -sin(phi), cos(phi)));

				//两个方向旋转
				pts.push_back(cv::Point3f(cos(theta_left), 0, sin(theta_left)));
				pts.push_back(cv::Point3f(sin(phi_up)*sin(theta_left), cos(phi_up), -sin(phi_up)*cos(theta_left)));
				pts.push_back(cv::Point3f(-cos(phi_up)*sin(theta_left), sin(phi_up), cos(phi_up)*cos(theta_left)));


				cv::Mat revert = cv::Mat(pts).reshape(1).t();

				cv::Mat changed(revert*curPt);

				cv::Mat_<double> changed_double;
				changed.convertTo(changed_double, CV_64F);

				x = changed_double.at<double>(0, 0);
				y = changed_double.at<double>(1, 0);
				z = changed_double.at<double>(2, 0);

				//std::cout << curPt << std::endl
				//	<<revert<<std::endl;
			}

			//Convert from unit sphere cooradinate to the parameter sphere cooradinate
			Theta_sphere = acos(z);
			Phi_sphere = cvFastArctan(y, x);//return value in Angle
			Phi_sphere = Phi_sphere*PI / 180;//Convert from Angle to Radian


			switch (camProjMode)
			{
			case STEREOGRAPHIC:
				foval = radius / (2 * tan(camerFieldAngle / 4));
				p = 2 * foval*tan(Theta_sphere / 2);
				break;
			case EQUIDISTANCE:
				foval = radius / (camerFieldAngle / 2);
				p = foval*Theta_sphere;
				break;
			case EQUISOLID:
				foval = radius / (2 * sin(camerFieldAngle / 4));
				p = 2 * foval*sin(Theta_sphere / 2);
				break;
			case ORTHOGONAL:
				foval = radius / sin(camerFieldAngle / 2);
				p = foval*sin(Theta_sphere);
				break;
			default:
				cout << "The camera mode hasn't been choose!" << endl;
			}
			//Convert from parameter sphere cooradinate to fish-eye polar cooradinate
			//p = sin(Theta_sphere);
			theta = Phi_sphere;

			//Convert from fish-eye polar cooradinate to cartesian cooradinate
			x_cart = p*cos(theta);
			y_cart = p*sin(theta);

			//double R = radius / sin(camerFieldAngle / 2);

			//Convert from cartesian cooradinate to image cooradinate
			u = x_cart + center.x;
			v = -y_cart + center.y;

			pt = Point(u, v);

			if (!pt.inside(imgArea))
			{
				continue;
			}

			_retImg.at<Vec3b>(j, i) = _imgOrg.at<Vec3b>(pt);

		}
	}

	//imshow("org", _imgOrg);
	//imshow("ret", _retImg);
	//cv::waitKey();
#ifdef _DEBUG_
	cv::namedWindow("Corrected Image", CV_WINDOW_AUTOSIZE);
	imshow("Corrected Image", retImg);
	cv::waitKey();
#endif
	//imwrite("ret.jpg", retImg);
	return retImg;
}
double corrector::func(double l, double phi)
{
	double result = (l / 2 - 1)*cos(phi) - sin(phi) + 1;
	return result;
}
double corrector::getPhi(double l)
{
	double head = 0;
	double tail = 0;
	double mid = 0;
	double result = 0;
	if (l >= 0 && l < 2)
	{
		head = 0;
		tail = PI / 2;
		mid = head;
		result = func(l, mid);
		while (abs(result)>LIMIT)
		{
			mid = (tail + head) / 2;
			result = func(l, mid);

			if (result > 0)
			{
				head = mid;
			}
			else
			{
				tail = mid;
			}
		}
	}
	else
	{
		head = PI / 2;
		tail = PI;
		mid = tail;
		result = func(l, mid);
		while (abs(result) > LIMIT)
		{
			mid = (tail + head) / 2;
			result = func(l, mid);
			if (result < 0)
			{
				head = mid;
			}
			else
			{
				tail = mid;
			}
		}
	}
	return mid;
}

/*********************w is variable********************************/
Mat corrector::latitudeCorrection4(Mat imgOrg, Point2i center, int radius, double w_longtitude, double w_latitude, distMapMode distMap, double theta_left, double phi_up, double camerFieldAngle, camMode camProjMode)
{
	if (!(camerFieldAngle > 0 && camerFieldAngle <= PI))
	{
		cout << "The parameter \"camerFieldAngle\" must be in the interval (0,PI]." << endl;
		return Mat();
	}
	double rateOfWindow = 0.9;

	//int width = imgOrg.size().width*rateOfWindow;
	//int height = width;

	//int width = max(imgOrg.cols, imgOrg.rows);
	int width = 512;
	int height = width;
	//int height = imgOrg.rows;


	Size imgSize(width, height);
	int center_x = imgSize.width / 2;
	int center_y = imgSize.height / 2;

	Mat retImg(imgSize, CV_8UC3, Scalar(0, 0, 0));

	double dx = camerFieldAngle / imgSize.width;
	double dy = camerFieldAngle / imgSize.height;

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
	double u, v;
	Point pt, pt1, pt2, pt3, pt4;

	//Image cooradinate of imgRet
	int u_latitude, v_latitude;
	Rect imgArea(0, 0, imgOrg.cols, imgOrg.rows);

	//offset of imgRet Origin
	double longitude_offset, latitude_offset;
	longitude_offset = (PI - camerFieldAngle) / 2;
	latitude_offset = (PI - camerFieldAngle) / 2;

	double foval = 0.0;//焦距


	cv::Mat_<Vec3b> _retImg = retImg;
	cv::Mat_<Vec3b> _imgOrg = imgOrg;

	//according to the camera type to do the calibration
	double  limi_latitude = 2 * auxFunc(w_latitude, 0);
	double  limi_longtitude = 2 * auxFunc(w_longtitude, 0);
	for (int j = 0; j < imgSize.height; j++)
	{

		for (int i = 0; i < imgSize.width; i++)
		{
			Point3f tmpPt(i - center_x, center_y - j, 600);//最后一个参数用来修改成像面的焦距
			double normPt = norm(tmpPt);

			switch (distMap)
			{
			case PERSPECTIVE:

				tmpPt.x /= normPt;
				tmpPt.y /= normPt;
				tmpPt.z /= normPt;

				x = tmpPt.x;
				y = tmpPt.y;
				z = tmpPt.z;

				break;
			case LATITUDE_LONGTITUDE:

				//latitude = latitude_offset + j*dy;

				latitude = getPhi1((double)j*limi_latitude / imgSize.height, w_latitude);
				//longitude = getPhi1((double)i * limi_longtitude / imgSize.width,w_longtitude);

				//latitude = latitude_offset + j*dy;
				longitude = longitude_offset + i*dx;
				//Convert from latitude cooradinate to the sphere cooradinate
				x = -sin(latitude)*cos(longitude);
				y = cos(latitude);
				z = sin(latitude)*sin(longitude);

				break;
			default:
				break;
			}

			if (distMap == PERSPECTIVE)
			{
				//double theta = PI/4;
				//double phi = -PI/2;
				cv::Mat curPt(cv::Point3f(x, y, z));
				std::vector<cv::Point3f> pts;

				//向东旋转地球
				//pts.push_back(cv::Point3f(cos(theta), 0, -sin(theta)));
				//pts.push_back(cv::Point3f(0, 1, 0));
				//pts.push_back(cv::Point3f(sin(theta), 0, cos(theta)));

				//向南旋转地球
				//pts.push_back(cv::Point3f(1, 0, 0));
				//pts.push_back(cv::Point3f(0, cos(phi), sin(phi)));
				//pts.push_back(cv::Point3f(0, -sin(phi), cos(phi)));

				//两个方向旋转
				pts.push_back(cv::Point3f(cos(theta_left), 0, sin(theta_left)));
				pts.push_back(cv::Point3f(sin(phi_up)*sin(theta_left), cos(phi_up), -sin(phi_up)*cos(theta_left)));
				pts.push_back(cv::Point3f(-cos(phi_up)*sin(theta_left), sin(phi_up), cos(phi_up)*cos(theta_left)));


				cv::Mat revert = cv::Mat(pts).reshape(1).t();

				cv::Mat changed(revert*curPt);

				cv::Mat_<double> changed_double;
				changed.convertTo(changed_double, CV_64F);

				x = changed_double.at<double>(0, 0);
				y = changed_double.at<double>(1, 0);
				z = changed_double.at<double>(2, 0);

				//std::cout << curPt << std::endl
				//	<<revert<<std::endl;
			}

			//Convert from unit sphere cooradinate to the parameter sphere cooradinate
			Theta_sphere = acos(z);
			Phi_sphere = cvFastArctan(y, x);//return value in Angle
			Phi_sphere = Phi_sphere*PI / 180;//Convert from Angle to Radian


			switch (camProjMode)
			{
			case STEREOGRAPHIC:
				foval = radius / (2 * tan(camerFieldAngle / 4));
				p = 2 * foval*tan(Theta_sphere / 2);
				break;
			case EQUIDISTANCE:
				foval = radius / (camerFieldAngle / 2);
				p = foval*Theta_sphere;
				break;
			case EQUISOLID:
				foval = radius / (2 * sin(camerFieldAngle / 4));
				p = 2 * foval*sin(Theta_sphere / 2);
				break;
			case ORTHOGONAL:
				foval = radius / sin(camerFieldAngle / 2);
				p = foval*sin(Theta_sphere);
				break;
			default:
				cout << "The camera mode hasn't been choose!" << endl;
			}
			//Convert from parameter sphere cooradinate to fish-eye polar cooradinate
			//p = sin(Theta_sphere);
			theta = Phi_sphere;

			//Convert from fish-eye polar cooradinate to cartesian cooradinate
			x_cart = p*cos(theta);
			y_cart = p*sin(theta);

			//double R = radius / sin(camerFieldAngle / 2);

			//Convert from cartesian cooradinate to image cooradinate
			u = x_cart + center.x;
			v = -y_cart + center.y;

			pt = Point(u, v);

			if (!pt.inside(imgArea))
			{
				continue;
			}
			else
			{
				_retImg.at<Vec3b>(j, i) = _imgOrg.at<Vec3b>(pt);
			}


		}
	}

	//imshow("org", _imgOrg);
	//imshow("ret", _retImg);
	//cv::waitKey();
#ifdef _DEBUG_
	cv::namedWindow("Corrected Image", CV_WINDOW_AUTOSIZE);
	imshow("Corrected Image", retImg);
	cv::waitKey();
#endif
	imwrite("ret.jpg", retImg);
	return retImg;
}
double corrector::func1(double l, double phi, double w)
{
	static double limit = auxFunc(w, 0);
	double result = l - limit + auxFunc(w, phi);
	return result;
}
double corrector::getPhi1(double l, double w)
{
	int N_lim = 100;
	int N = 0;
	static double lim = auxFunc(w, 0);

	double head = 0;
	double tail = 0;
	double mid = 0;
	double result = 0;
	if (l >= 0 && l < lim)
	{
		head = 0;
		tail = PI / 2;
		mid = head;
		result = func1(l, mid, w);
		while (abs(result)>LIMIT&&N++ < N_lim)
		{
			mid = (tail + head) / 2;
			result = func1(l, mid, w);

			if (result > 0)
			{
				head = mid;
			}
			else
			{
				tail = mid;
			}
		}
	}
	else
	{
		N = 0;
		head = PI / 2;
		tail = PI;
		mid = tail;
		result = func1(l, mid, w);
		while (abs(result) > LIMIT&&N++ < N_lim)
		{
			mid = (tail + head) / 2;
			result = func1(l, mid, w);
			if (result > 0)
			{
				head = mid;
			}
			else
			{
				tail = mid;
			}
		}
	}
	return mid;
}

double corrector::auxFunc(double w, double phi)
{
	double l = sin(w)*sqrt(cos(phi)*cos(phi) + (1 - sin(phi))*(1 - sin(phi))) / sin(PI - w - atan((1 - sin(phi)) / abs(cos(phi))));
	if (phi > PI / 2)
		l = -l;
	return l;
}

/************************w is variable, and Forward map*/
Mat corrector::latitudeCorrection5(Mat imgOrg, Point2i center, int radius, double w_longtitude, double w_latitude, distMapMode distMap, double theta_left, double phi_up, double camerFieldAngle, camMode camProjMode)
{
	if (!(camerFieldAngle > 0 && camerFieldAngle <= PI))
	{
		cout << "The parameter \"camerFieldAngle\" must be in the interval (0,PI]." << endl;
		return Mat();
	}
	double rateOfWindow = 0.9;

	//int width = imgOrg.size().width*rateOfWindow;
	//int height = width;

	//int width = max(imgOrg.cols, imgOrg.rows);
	int width = 512;
	int height = width;
	//int height = imgOrg.rows;


	Size imgSize(width, height);
	int center_x = imgSize.width / 2;
	int center_y = imgSize.height / 2;

	Mat retImg(imgSize, CV_8UC3, Scalar(0, 0, 0));

	double dx = camerFieldAngle / imgSize.width;
	double dy = camerFieldAngle / imgSize.height;

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
	double u, v;
	Point pt, pt1, pt2, pt3, pt4;

	//Image cooradinate of imgRet
	int u_longtitude, v_latitude;
	Rect imgArea(0, 0, imgOrg.cols, imgOrg.rows);

	//offset of imgRet Origin
	double longitude_offset, latitude_offset;
	longitude_offset = (PI - camerFieldAngle) / 2;
	latitude_offset = (PI - camerFieldAngle) / 2;

	double foval = 0.0;//焦距


	cv::Mat_<Vec3b> _retImg = retImg;
	cv::Mat_<Vec3b> _imgOrg = imgOrg;

	int left, top;
	left = center.x - radius;
	top = center.y - radius;
	for (int j = top; j < top + 2 * radius; j++)
	{
		for (int i = left; i < left + 2 * radius; i++)
		{
			if (pow(i - center.x, 2) + pow(j - center.y, 2) > pow(radius, 2))
				continue;
			//Origin image cooradinate in pixel
			u = i;
			v = j;

			//Convert to cartiesian cooradinate in unity circle
			x_cart = (u - center.x);
			y_cart = -(v - center.y);

			//convert to polar axes
			theta = cvFastArctan(y_cart, x_cart)*PI / 180;
			p = sqrt(pow(x_cart, 2) + pow(y_cart, 2));

			//convert to sphere surface parameter cooradinate


			Theta_sphere = p*(camerFieldAngle / 2) / radius;
			Phi_sphere = theta;

			//convert to sphere surface 3D cooradinate
			x = sin(Theta_sphere)*cos(Phi_sphere);
			y = sin(Theta_sphere)*sin(Phi_sphere);
			z = cos(Theta_sphere);

			//convert to latitiude  cooradinate
			latitude = acos(y);
			longitude = cvFastArctan(z, -x)*PI / 180;

			//transform the latitude to pixel cooradinate
			double  limi_latitude = auxFunc(w_latitude, 0);
			double l = 0;
			if (latitude >= 0 && latitude < PI / 2)
			{
				l = limi_latitude - sin(w_latitude)*sqrt(cos(latitude)*cos(latitude) + (1 - sin(latitude))*(1 - sin(latitude))) / sin(PI - w_latitude - atan((1 - sin(latitude)) / abs(cos(latitude))));
			}
			else
			{
				l = limi_latitude + sin(w_latitude)*sqrt(cos(latitude)*cos(latitude) + (1 - sin(latitude))*(1 - sin(latitude))) / sin(PI - w_latitude - atan((1 - sin(latitude)) / abs(cos(latitude))));
			}
			u_longtitude = ((longitude - longitude_offset) / dx);
			// = (latitude - latitude_offset) / dy;
			v_latitude = l*imgSize.height / (2 * limi_latitude);

			if (u_longtitude < 0 || u_longtitude >= imgSize.height || v_latitude < 0 || v_latitude >= imgSize.width)
				continue;

			//perform the map from the origin image to the latitude map image
			_retImg.at<cv::Vec3b>(v_latitude, u_longtitude) = imgOrg.at<cv::Vec3b>(j, i);
		}
	}

	//imshow("org", _imgOrg);
	//imshow("ret", _retImg);
	//cv::waitKey();
#ifdef _DEBUG_
	cv::namedWindow("Corrected Image", CV_WINDOW_AUTOSIZE);
	imshow("Corrected Image", retImg);
	cv::waitKey();
#endif
	imwrite("ret.jpg", retImg);
	return retImg;
}

#pragma endregion


#pragma region 图像拼接相关

#pragma endregion