#include "viewer.h"

viewer::viewer(Mat inputImg)
{
	Size size(VIEWER_WIDTH, VIEWER_HEIGHT);
	paronoma = inputImg.clone();
	window = Mat(size.height, size.width, inputImg.type());
	angleH = 0;
	angleV = PI / 2;
	winname = "window";
	winname_paronomaWithOutline = "paronomaWithOutline";
	distance = 300;

}

Mat viewer::getWindow()
{
	return window;
}

void viewer::showWindow()
{
	if (window.empty())
	{
		cout << "The window img is empty!" << endl;
		return;
	}
	updataWindow();
	cv::namedWindow(winname, CV_WINDOW_AUTOSIZE);
	cv::setMouseCallback(winname, onMouse, this);
	refreshWindow();
	cv::waitKey(0);
}

void viewer::updataWindow()
{
	paronomaWithOutline = paronoma.clone();
	//获取显示区域的尺寸
	Size dispSize = window.size();

	int center_x = dispSize.width/ 2;
	int center_y = dispSize.height / 2;

	//coordinate for latitude map
	double latitude;
	double longitude;

	//unity sphere coordinate 
	double x, y, z;

	//parameter cooradinate of sphere coordinate
	double Theta_sphere;
	double Phi_sphere;

	cv::Mat_<Vec3b> _retImg = window;
	cv::Mat_<Vec3b> _imgOrg = paronoma;

	cout << "[Processing ";

	double percent = 0.0;

	int count = dispSize.height / 80;
	for (int j = 0; j < dispSize.height; j++)
	{
		for (int i = 0; i < dispSize.width; i++)
		{
			Point3d tmpPt(i - center_x, center_y - j, distance);//最后一个参数用来修改成像面到单位球面的距离

			double normPt = norm(tmpPt);

			//求出单位圆上的点坐标
			tmpPt.x /= normPt;
			tmpPt.y /= normPt;
			tmpPt.z /= normPt;

			Point3d ret = navigationHV(tmpPt, angleH, angleV);

			x = ret.x;
			y = ret.y;
			z = ret.z;

			//Convert from unit sphere cooradinate to the parameter sphere cooradinate
			Theta_sphere = acos(z);//acos() range is 0~pi
			Phi_sphere = cvFastArctan(y, x);//return value in Angle cvFastArctan() range is: 0~360
			Phi_sphere = Phi_sphere*PI / 180;//Convert from Angle to Radian

			latitude = Theta_sphere;
			longitude = Phi_sphere;


			int u = (longitude) / (2 * PI)*_imgOrg.size().width;
			int v = (latitude) / (PI)*_imgOrg.size().height;

			u = u%_imgOrg.size().width;
			v = v%_imgOrg.size().height;

			Point pt(v, u);

			if (pt.inside(Rect(0, 0, _imgOrg.size().height, _imgOrg.size().width + 1)))
			{
				_retImg.at<Vec3b>(j, i) = _imgOrg.at<Vec3b>(v, u);
				paronomaWithOutline.at<Vec3b>(v, u) = Vec3b(255, 255, 255);
	
			}
		}
		if (j%count == 0)
			cout << ".";
	}
	cout << "]" << endl;
	resize(paronomaWithOutline,paronomaWithOutline,Size(VIEWER_WIDTH, VIEWER_HEIGHT));
}
Point3d viewer::navigationHV(Point3d orgPt, double angleH, double angleV)
{
	Mat cvtMatH(3, 3, CV_64F, Scalar(0));
	cvtMatH.at<double>(0, 0) = cos(angleH);
	cvtMatH.at<double>(0, 2) = -sin(angleH);
	cvtMatH.at<double>(1, 1) = 1;
	cvtMatH.at<double>(2, 0) = sin(angleH);
	cvtMatH.at<double>(2, 2) = cos(angleH);

	Mat cvtMatV(3, 3, CV_64F, Scalar(0));
	cvtMatV.at <double>(0, 0) = 1;
	cvtMatV.at<double>(1, 1) = cos(angleV);
	cvtMatV.at<double>(1, 2) = -sin(angleV);
	cvtMatV.at<double>(2, 1) = sin(angleV);
	cvtMatV.at<double>(2, 2) = cos(angleV);

	Mat cvtMat = cvtMatV*cvtMatH;

	Mat org(orgPt);
	cv::Mat_<double> dOrg;
	org.convertTo(dOrg, CV_64F);

	cv::Mat_<double> ret(3, 1, CV_64F);
	ret = cvtMat*dOrg;

	return Point3d(ret);
}

void viewer::refreshWindow()
{
	if (window.empty())
		return;
	imshow(winname, window);

	if (paronomaWithOutline.empty())
		return;
	imshow(winname_paronomaWithOutline, paronomaWithOutline);
}
void viewer::onMouse(int event, int x, int y, int, void * params)
{
	viewer *pV = (viewer*)params;
	Point pt(x, y);
	Size size = pV->window.size();

	Rect left(0, 0, size.width / 4, size.height);
	Rect right(size.width * 3 / 4, 0, size.width / 4, size.height);
	Rect top(size.width / 4, 0, size.width / 2, size.height / 2);
	Rect bottom(size.width / 4, size.height / 2, size.width / 2, size.height / 2);

	const double delta = PI / 8;
	const double limitH = 2 * PI;
	const double limitV = PI;
	const double zoomDelta = 50;
	switch (event)
	{
	case EVENT_LBUTTONDOWN:
		if (pt.inside(left))
		{
			pV->angleH = pV->angleH + delta;
			if (pV->angleH > limitH)
				pV->angleH = pV->angleH - limitH;
			cout << "Move Left" << endl;
		}
		else if (pt.inside(right))
		{
			pV->angleH = pV->angleH - delta;
			if (pV->angleH < 0)
				pV->angleH = pV->angleH + limitH;
			cout << "Move Right" << endl;
		}
		else if (pt.inside(top))
		{
			if (pV->angleV - delta>0)
				pV->angleV = pV->angleV - delta;
			else
				pV->angleV = 0;

			cout << "Move Up" << endl;
		}
		else
		{
			if (pV->angleV + delta<limitV)
				pV->angleV = pV->angleV + delta;
			else
				pV->angleV = limitV;
			cout << "Move Down" << endl;
		}

		pV->updataWindow();
		pV->refreshWindow();

		break;
	case EVENT_MBUTTONDOWN:
		cout << "Zoom In" << endl;

		pV->distance = pV->distance + zoomDelta;
		pV->updataWindow();
		pV->refreshWindow();
		break;

	case EVENT_RBUTTONDOWN:
		cout << "Zoom Out" << endl;

		pV->distance = pV->distance - zoomDelta;
		if (pV->distance < 250)
		{
			pV->distance = 250;
		}
		pV->updataWindow();
		pV->refreshWindow();
		break;
	default:
		break;
	}

}
