#include "findCircleParameter.h"

#pragma region 与变角度线扫描法相关的变量声明
//圆提取窗口标题
string findCircleParameter::win_name = "Circle Extraction";

//变角度线扫描法，扫描倾角分割系数
string findCircleParameter::N_trackbar_name = "N(0-15)";

//变角度线扫描法阈值设定值
string findCircleParameter::thresholdValue_trackbar_name = "Threshold(0-255)";

//变角度线扫描法的角度方向数初值
int findCircleParameter::N_slider_value = 5;

//变角度线扫描法的角度方向数最大设定值
int findCircleParameter::N_max_value = 15;

//线扫描的阈值
int findCircleParameter::thresholdValue_slider_value = 40;

//线扫描阈值最大设定值
int findCircleParameter::thresholdValue_max_value = 255;

//存放识别出的圆的中心坐标(图像坐标系下)
Point2i findCircleParameter::center = Point2i(-1, -1);

//存放识别出的圆的半径大小
int findCircleParameter::radius = -1;

//存放原图
Mat findCircleParameter::image = Mat();
#pragma endregion

#pragma region 验证部分变量初始化
//存放线条上点的坐标
std::vector<std::vector<cv::Point>> findCircleParameter::lines;

//验证窗口标题
std::string findCircleParameter::check_win_name = "Check Verify";

//
std::vector<cv::Point> findCircleParameter::points;

//鱼眼镜头的视场角
const double findCircleParameter::FOV = PI;
#pragma endregion

#pragma region 为了便于显示而计算的图片显示尺寸
int findCircleParameter::width_disp_img = -1;
int findCircleParameter::height_disp_img = -1;

#pragma endregion


//初始化识别图，导入待识别图像
bool findCircleParameter::init(Mat img)
{
	image = img;
	if (image.data)
	{
		height_disp_img = 512;
		width_disp_img = (image.cols / (double)image.rows)*height_disp_img;

		return true;
	}
	return false;
}

//开始识别圆
void findCircleParameter::findCircle()
{
	namedWindow(win_name,CV_WINDOW_NORMAL);
	resizeWindow(win_name, width_disp_img, height_disp_img+100);
	createTrackbar(N_trackbar_name, win_name, &N_slider_value, N_max_value, On_N_trackbar);
	createTrackbar(thresholdValue_trackbar_name, win_name, &thresholdValue_slider_value, thresholdValue_max_value, On_threshold_trackbar);
	On_N_trackbar(N_slider_value, 0);
	On_threshold_trackbar(thresholdValue_slider_value, 0);
	waitKey();
	destroyWindow(win_name);
}

//检验是否有效
void findCircleParameter::checkVarify()
{
	namedWindow(check_win_name, CV_WINDOW_NORMAL);
	resizeWindow(check_win_name, width_disp_img, height_disp_img);
	imshow(check_win_name, image);
	setMouseCallback(check_win_name, onMouse);
	waitKey();
	cv::destroyWindow(check_win_name);
}

//获取检测到的圆的参数
bool findCircleParameter::getCircleParatemer(Point2i & centerPos, int& r)
{
	if (center != Point2i(-1, -1) && radius != -1)
	{
		centerPos = center;
		r = radius;
		return true;
	}
	return false;
	
}


//光标回调函数
void findCircleParameter::onMouse(int event, int x, int y, int, void* params)
{
	Mat src = image.clone();
	cv::Point pt(x, y);
	switch (event)
	{
	case cv::EVENT_LBUTTONDOWN:
		cv::circle(src, pt, src.cols*0.005, cv::Scalar(0, 255, 0), -1);
		cv::imshow(check_win_name, src);
		points.push_back(pt);
		if (2 == points.size())
		{
			findPoints(center, radius, points);
			std::vector<Point>::iterator it = points.begin();
			while (it != points.end() - 1)
			{
				cv::circle(src, *it, src.cols*0.003, cv::Scalar(0, 0, 255), -1);
				cv::circle(src, *(it + 1), src.cols*0.003, cv::Scalar(0, 0, 255), -1);

				line(src, *it, *(it + 1), Scalar(0, 255, 255), src.cols*0.002);
				++it;
			}
			cv::imshow(check_win_name, src);
			lines.push_back(points);
			points.clear();
		}
		break;
	case cv::EVENT_MOUSEMOVE:
		//cout << "(x, y) = (" << x << ", " << y << ")" << endl;
	default:
		;
	}
}

void findCircleParameter::findPoints(Point2i center, int radius, std::vector<cv::Point> &points, camMode projMode)
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
		cout << "[x, y, z] = " << *itSphere << endl
			<< "norm = " << sqrt(temp) << endl;

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
	while (l++ <= count)
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

findCircleParameter::~findCircleParameter()
{
}

//为确定鱼眼圆形有效区域参数而设置的回调函数，供OpenCV使用
void findCircleParameter::On_N_trackbar(int N_slider_value, void* params)
{
	cout << endl;
	cout << "N_Slider" << N_slider_value << endl;
	cout << "Threshold_Slider" << thresholdValue_slider_value << endl;
	//用变角度线扫描法取求圆形有效区域的圆心和半径的参数
	if (image.data)
		revisedScanLineMethod(image, center, radius, thresholdValue_slider_value, N_slider_value);
}

//为确定鱼眼圆形有效区域参数而设置的回调函数，供OpenCV使用
void findCircleParameter::On_threshold_trackbar(int thresholdValue_slider_value, void* params)
{
	cout << endl;
	cout << "N_Slider: " << N_slider_value << endl;
	cout << "Threshold_Slider: " << thresholdValue_slider_value << endl;
	//用变角度线扫描法取求圆形有效区域的圆心和半径的参数
	if (image.data)
		revisedScanLineMethod(image, center, radius, thresholdValue_slider_value, N_slider_value);
}

//变角度线扫描法——改进后的线扫描法
void findCircleParameter::revisedScanLineMethod(Mat imgOrg, Point2i& center, int& radius, int threshold, int N)
{
	Mat src, gray;
	src = imgOrg.clone();
	cvtColor(src, gray, CV_BGR2GRAY);

	vector<Point> points;
	vector<double> distance;

	Size imgSize = src.size();

	int x, y;
	double theta = 0;

	for (int n = 0; n < 2 * N; n++, theta = PI*n / (2 * N))
	{
		//if (n == N||n==0) continue;
		int min1, min2;
		min1 = min2 = 255;
		int max1, max2;
		max1 = max2 = 0;
		int radius = 0;
		Point ptMax1(0, 0), ptMax2(0, 0);
		Point ptMin1(0, 0), ptMin2(0, 0);
		int flag = 0;

		double minVal, maxVal;

		if (0 == n)
		{
			for (int i = 0; i < imgSize.height; i++)
			{
				minMaxLoc(gray.row(i), &minVal, &maxVal, &ptMin1, &ptMax1);
				if ((maxVal - minVal)>threshold)
				{
					flag++;

					ptMax1.y = i;
					//cout << "horizontal top:" << endl;
					//cout << "ptMax1=(" << ptMax1.x << ", " << ptMax1.y << ")" << endl;
					points.push_back(ptMax1);
					goto top_label;
				}
			}
		top_label:

#ifdef _SHOW_POINTS_
			circle(src, ptMax1, 5, Scalar(0, 255, 255), -1);
			imshow("src", src);
			waitKey();
#endif

			for (int i = imgSize.height - 1; i >= 0; i--)
			{
				minMaxLoc(gray.row(i), &minVal, &maxVal, &ptMin2, &ptMax2);
				if ((maxVal - minVal) > threshold)
				{
					flag++;

					ptMax2.y = i;
					//cout << "horizontal bottom:" << endl;
					//cout << "ptMax2=(" << ptMax2.x << ", " << ptMax2.y << ")" << endl;

					//src.row(i) = Scalar(0, 0, 255);
					//src.row(i + 1) = Scalar(0, 0, 255);

					points.push_back(ptMax2);
					goto bottom_label;
				}
			}
		bottom_label:

#ifdef _SHOW_POINTS_
			circle(src, ptMax2, 5, Scalar(0, 255, 255), -1);
			line(src, ptMax1, ptMax2, Scalar(192, 192, 0), 2);
			imshow("src", src);
			waitKey();
#endif
			if (flag == 2)
			{
				distance.push_back(sqrt(pow(ptMax1.x - ptMax2.x, 2) + pow(ptMax1.y - ptMax2.y, 2)));
			}
			else if (flag == 1)
			{
				points.pop_back();
			}
		}
		else if (0 < n&&n < N)
		{
			for (int i = 0; i < imgSize.width; i++)
			{
				for (int j = 0; j <= i; j++)
				{
					x = j;
					y = -tan(theta)*(x - i);

					Point ptCur(x, y);
					if (!ptCur.inside(Rect(0, 0, imgSize.width, imgSize.height)))
					{
						continue;
					}

					uchar I = gray.at<uchar>(ptCur);

					if (I > max1)
					{
						max1 = I;
						ptMax1 = ptCur;
					}
					if (I < min1)
					{
						min1 = I;
					}

					if (abs(max1 - min1) > threshold)
					{
						flag++;
						//cout << "jump outer1" << endl;
						//cout << "ptMax1=(" << ptMax1.x << ", " << ptMax1.y << ")" << endl;
						points.push_back(ptMax1);

						/*						Point start, end;
						for (int k = 0; k <= i; k++)
						{
						x = k;
						y = -tan(theta)*(x - i);
						if (k == 0)
						{
						start = Point(x, y);
						}
						else if (k == i)
						{
						end = Point(x, y);
						}


						}
						line(src, start, end, Scalar(0, 0, 255), 2);*/

						goto outer1;
					}
				}
			}
		outer1:

#ifdef _SHOW_POINTS_
			circle(src, ptMax1, 5, Scalar(0, 255, 255), -1);
			imshow("src", src);
			waitKey();
#endif

			for (int i = imgSize.width - 1; i >= 0; i--)
			{
				for (int j = i; j < imgSize.width; j++)
				{
					x = j;
					y = imgSize.height - 1 - tan(theta)*(x - i);

					Point ptCur(x, y);

					if (!ptCur.inside(Rect(0, 0, imgSize.width, imgSize.height)))
					{
						continue;
					}
					uchar I = gray.at<uchar>(ptCur);

					if (I > max2)
					{
						max2 = I;
						ptMax2 = ptCur;
					}
					if (I < min2)
					{
						min2 = I;
					}

					if (abs(max2 - min2) > threshold)
					{
						flag++;
						//cout << "jump outer2" << endl;
						//cout << "ptMax2=(" << ptMax2.x << ", " << ptMax2.y << ")" << endl;
						points.push_back(ptMax2);

						//Point start, end;
						//for (int k = i; k < imgSize.width; k++)
						//{
						//	x = k;
						//	y = imgSize.height - 1 - tan(theta)*(x - i);
						//	if (k == i)
						//	{
						//		start = Point(x, y);
						//	}
						//	else if (k == imgSize.width-1)
						//	{
						//		end = Point(x, y);
						//	}


						//}
						//line(src, start, end, Scalar(0, 0, 255), 2);

						goto outer2;
					}
				}
			}
		outer2:
			;

#ifdef _SHOW_POINTS_
			circle(src, ptMax2, 5, Scalar(0, 255, 255), -1);
			line(src, ptMax1, ptMax2, Scalar(192, 192, 0), 2);
			imshow("src", src);
			waitKey();
#endif
			if (flag == 2)
			{
				distance.push_back(sqrt(pow(ptMax1.x - ptMax2.x, 2) + pow(ptMax1.y - ptMax2.y, 2)));
			}
			else if (flag == 1)
			{
				points.pop_back();
			}

		}
		else if (N == n)
		{
			for (int i = 0; i < imgSize.width; i++)
			{
				minMaxLoc(gray.col(i), &minVal, &maxVal, &ptMin1, &ptMax1);
				if ((maxVal - minVal)>threshold)
				{
					flag++;
					ptMax1.x = i;
					//cout << "vertical left:" << endl;
					//cout << "ptMax1=(" << ptMax1.x << ", " << ptMax1.y << ")" << endl;

					//src.col(i) = Scalar(0, 0, 255);
					//src.col(i - 1) = Scalar(0, 0, 255);
					points.push_back(ptMax1);
					goto left_label;
				}
			}
		left_label:

#ifdef _SHOW_POINTS_
			circle(src, ptMax1, 5, Scalar(0, 255, 255), -1);
			imshow("src", src);
			waitKey();
#endif

			for (int i = gray.cols - 1; i >= 0; i--)
			{
				minMaxLoc(gray.col(i), &minVal, &maxVal, &ptMin2, &ptMax2);
				if ((maxVal - minVal) > threshold)
				{
					flag++;
					ptMax2.x = i;
					//cout << "vertical right:" << endl;
					//cout << "ptMax1=(" << ptMax2.x << ", " << ptMax2.y << ")" << endl;
					points.push_back(ptMax2);

					//src.col(i) = Scalar(0, 0, 255);
					//src.col(i + 1) = Scalar(0, 0, 255);

					goto right_label;
				}
			}

		right_label:

#ifdef _SHOW_POINTS_
			circle(src, ptMax2, 5, Scalar(0, 255, 255), -1);
			line(src, ptMax1, ptMax2, Scalar(192, 192, 0), 2);
			imshow("src", src);
			waitKey();
#endif
			if (flag == 2)
			{
				distance.push_back(sqrt(pow(ptMax1.x - ptMax2.x, 2) + pow(ptMax1.y - ptMax2.y, 2)));
			}
			else if (flag == 1)
			{
				points.pop_back();
			}

		}
		else if (N < n&&n < 2 * N)
		{
			for (int i = 0; i < imgSize.width; i++)
			{
				for (int j = 0; j <= i; j++)
				{
					x = j;
					y = imgSize.height - 1 - tan(theta)*(x - i);

					Point ptCur(x, y);
					if (!ptCur.inside(Rect(0, 0, imgSize.width, imgSize.height)))
					{
						continue;
					}
					uchar I = gray.at<uchar>(ptCur);

					if (I > max1)
					{
						max1 = I;
						ptMax1 = ptCur;
					}
					if (I < min1)
					{
						min1 = I;
					}

					if (abs(max1 - min1) > threshold)
					{
						flag++;
						//cout << "jump outer3" << endl;
						//cout << "ptMax1=(" << ptMax1.x << ", " << ptMax1.y << ")" << endl;
						points.push_back(ptMax1);

						//Point start, end;
						//for (int k = 0; k <= i; k++)
						//{
						//	x = k;
						//	y = imgSize.height - 1 - tan(theta)*(x - i);

						//	if (k == 0)
						//	{
						//		start = Point(x, y);
						//	}
						//	else if (k == i)
						//	{
						//		end = Point(x, y);
						//	}
						//}
						//line(src, start, end, Scalar(0, 0, 255), 2);

						goto outer3;
					}
				}
			}
		outer3:

#ifdef _SHOW_POINTS_
			circle(src, ptMax1, 5, Scalar(0, 255, 255), -1);
			imshow("src", src);
			waitKey();
#endif

			for (int i = imgSize.width - 1 / 2; i >= 0; i--)
			{
				for (int j = i; j < imgSize.width; j++)
				{
					x = j;
					y = -tan(theta)*(x - i);

					Point ptCur(x, y);
					if (!ptCur.inside(Rect(0, 0, imgSize.width, imgSize.height)))
					{
						continue;
					}
					uchar I = gray.at<uchar>(ptCur);

					if (I > max2)
					{
						max2 = I;
						ptMax2 = ptCur;
					}
					if (I < min2)
					{
						min2 = I;
					}

					if (abs(max2 - min2) > threshold)
					{
						flag++;
						//cout << "jump outer4" << endl;
						//cout << "ptMax2=(" << ptMax2.x << ", " << ptMax2.y << ")" << endl;
						points.push_back(ptMax2);

						/*			Point start, end;
						for (int k = i; k < imgSize.width; k++)
						{
						x = k;
						y = -tan(theta)*(x - i);
						if (k == i)
						{
						start = Point(x, y);
						}
						else if (k == imgSize.width - 1)
						{
						end = Point(x, y);
						}


						}
						line(src, start, end, Scalar(0, 0, 255), 2);*/

						goto outer4;
					}
				}
			}
		outer4:

			;
#ifdef _SHOW_POINTS_
			circle(src, ptMax2, 5, Scalar(0, 255, 255), -1);
			line(src, ptMax1, ptMax2, Scalar(192, 192, 0), 2);
			imshow("src", src);
			waitKey();
#endif
			if (flag == 2)
			{
				distance.push_back(sqrt(pow(ptMax1.x - ptMax2.x, 2) + pow(ptMax1.y - ptMax2.y, 2)));
			}
			else if (flag == 1)
			{
				points.pop_back();
			}

		}
		else
		{
			cout << "The value of n is error!" << endl;
			break;
		}
	}


	//vector<Point>::iterator itero = points.begin();
	//ofstream of("points.txt", ios::trunc | ios::out);
	//while (itero != points.end())
	//{
	//	of << (*itero).x << ", " << (*itero).y << endl;
	//	itero++;
	//}
	//of.close(); 


	//find out validate points
	double mean = 0;
	vector<double>::iterator iter = distance.begin();
	while (iter != distance.end())
	{
		mean += *iter;
		iter++;
	}
	mean /= distance.size();

	vector<Point> validPoints;
	for (int i = 0; i < distance.size(); i++)
	{
		if (distance.at(i) < mean)
		{
			validPoints.push_back(points.at(2 * i));
			validPoints.push_back(points.at(2 * i + 1));
		}
	}

	//figure out the center and radius of the circle with Kasa method

	if (!CircleFitByKasa(validPoints, center, radius))
	{
		cout << "Revisied LineScan Method Failed, Because the Circle Fit Method failed!" << endl;
		return;
	}

	//#ifdef _DEBUG_
	cout << "Use the Revised ScanLine Method:" << endl
		<< "\tThe center is (" << center.x << ", "
		<< center.y << ")" << endl
		<< "\tThe radius is " << radius << endl;

	circle(src, center, radius, Scalar(0, 0, 255), src.cols / 300);
	circle(src, center, 5, Scalar(0, 255, 255), -1);

	//namedWindow("Revised ScanLine Method Result", CV_WINDOW_AUTOSIZE);
	//imshow("Revised ScanLine Method Result", src);
	imshow(win_name, src);
	//imwrite("Revised_Scan_ret.tiff", src);
	//waitKey();
	//#endif

}

//圆拟合函数，性能很好，但要防止拟合时出现奇异值的情况
bool findCircleParameter::CircleFitByKasa(vector<Point> validPoints, Point& center, int&	 radius)
{
	if (validPoints.size() <= 2)
	{
		cout << "The Circle fit failed, Because there is not enought validate points to use!" << endl;
		return false;
	}

	vector<Point3i> extendA;
	vector<int> extendB;
	vector<Point>::iterator iter = validPoints.begin();
	while (iter != validPoints.end())
	{
		extendA.push_back(Point3i((*iter).x, (*iter).y, 1));
		extendB.push_back((pow((*iter).x, 2) + pow((*iter).y, 2)));
		iter++;
	}
	Mat A = Mat(extendA).reshape(1);
	Mat	B = Mat(extendB).reshape(1);

	Mat_<double> dA, dB;
	Mat_<double> P(3, 1, CV_64F);
	A.convertTo(dA, CV_64F);
	B.convertTo(dB, CV_64F);
	P = dA.inv(CV_SVD)*dB;

	//cout << P << endl;

	double p1, p2, p3;
	p1 = P.at<double>(0, 0);
	p2 = P.at<double>(1, 0);
	p3 = P.at<double>(2, 0);

	center.x = p1 / 2;
	center.y = p2 / 2;
	radius = sqrt((pow(p1, 2) + pow(p2, 2)) / 4 + p3);

	//cout << center.x << endl << center.y << endl << radius << endl;
	return true;
}
